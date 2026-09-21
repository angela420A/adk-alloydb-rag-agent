from google import auth
from google.adk.models import google_llm
import os
import logging
from typing import Optional

from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmRequest, LlmResponse
from google.api_core.client_options import ClientOptions
from google.cloud import modelarmor_v1
from google.genai import types
from google.adk.plugins.base_plugin import BasePlugin

from agent.utils import config

logger = logging.getLogger(__name__)


def _extract_user_text(llm_request: LlmRequest) -> str:
    try:
        if llm_request.contents:
            for content in reversed(llm_request.contents):
                if content.role == "user":
                    for part in content.parts:
                        if hasattr(part, "text") and part.text:
                            return part.text
    except Exception as e:
        logger.error(f"[ModelArmorPlugin] Error extracting user text: {e}")
    return ""


def _extract_model_response(llm_response: LlmResponse) -> str:
    try:
        if llm_response.content and llm_response.content.parts:
            for part in llm_response.content.parts:
                if hasattr(part, "text") and part.text:
                    return part.text
    except Exception as e:
        logger.error(f"[ModelArmorPlugin] Error extracting model text: {e}")
    return ""


def _get_matched_filters(result) -> list[str]:
    matched_filters = []

    if result is None:
        return matched_filters

    try:
        filter_results = dict(result.sanitization_result.filter_results)
    except (AttributeError, TypeError):
        return matched_filters

    filter_attr_mapping = {
        "csam": "csam_filter_filter_result",
        "malicious_uris": "malicious_uri_filter_result",
        "pi_and_jailbreak": "pi_and_jailbreak_filter_result",
        "rai": "rai_filter_result",
        "sdp": "sdp_filter_result",
        "virus_scan": "virus_scan_filter_result",
    }

    for filter_name, filter_obj in filter_results.items():
        attr_name = filter_attr_mapping.get(filter_name)

        if not attr_name:
            if filter_name == "malicious_uris":
                attr_name = "malicious_uri_filter_result"
            else:
                attr_name = f"{filter_name}_filter_result"

            if hasattr(filter_obj, attr_name):
                filter_result = getattr(filter_obj, attr_name)

                if filter_name == "sdp" and hasattr(
                    filter_result,
                    "inspect_result"
                ):
                    if hasattr(filter_result.inspect_result, "match_state"):
                        if (
                            filter_result.inspect_result.match_state.name ==
                            "MATCH_FOUND"
                        ):
                            matched_filters.append("sdp")
                elif filter_name == "rai":
                    if hasattr(filter_result, "match_state"):
                        if filter_result.match_state.name == "MATCH_FOUND":
                            matched_filters.append("rai")
                    if hasattr(filter_result, "rai_filter_type_results"):
                        for sub_result in filter_result.rai_filter_type_results:
                            if hasattr(sub_result,
                                       "key") and hasattr(sub_result,
                                                          "value"):
                                if hasattr(sub_result.value, "match_state"):
                                    if (
                                        sub_result.value.match_state.name ==
                                        "MATCH_FOUND"
                                    ):
                                        matched_filters.append(
                                            f"rai:{sub_result.key}"
                                        )
                else:
                    if hasattr(filter_result, "match_state"):
                        if filter_result.match_state.name == "MATCH_FOUND":
                            matched_filters.append(filter_name)
    return matched_filters


class ModelArmorPlugin(BasePlugin):

    def __init__(self):
        super().__init__(name='model_armor_guard')
        self.project_id = os.getenv('GOOGLE_CLOUD_PROJECT', None)
        self.location = os.getenv('GOOGLE_CLOUD_LOCATION', None)
        self.template_id = os.getenv('MODEL_ARMOR_TEMPLATE_ID', None)

        if not self.template_id:
            logger.error(
                "[ModelArmorPlugin] can't not find template_id in env, or .env file is not set."
            )
            raise ValueError(
                "[ModelArmorPlugin] can't not find template_id in env, or .env file is not set.",
                "Run ./setup/setup_env.sh first.",
            )

        self.template_name = f"projects/{self.project_id}/locations/{self.location}/templates/{self.template_id}"
        self._client = None  # 在初始化時不建立連線，僅設為 None

        logger.info(
            f"[ModelArmorPlugin] Initialized with template: {self.template_id}"
        )

    @property
    def client(self) -> modelarmor_v1.ModelArmorClient:
        """
        延遲載入（Lazy Initialization）
        只有在 Runtime 實際被調用時，才會在當前環境中建立 ModelArmorClient
        """
        if self._client is None:
            self._client = modelarmor_v1.ModelArmorClient(
                transport="rest",
                client_options=ClientOptions(
                    api_endpoint=f"modelarmor.{self.location}.rep.googleapis.com"
                    # api_endpoint=f"modelarmor.googleapis.com"
                ),
            )
        return self._client

    def _blocked(self, result) -> bool:
        try:
            state = result.sanitization_result.filter_match_state
            return state.name == "MATCH_FOUND"
        except Exception:
            return False

    def _block_response(self, message: str) -> LlmResponse:
        return LlmResponse(
            content=types.
            Content(role="model",
                    parts=[types.Part.from_text(text=message)])
        )

    async def before_model_callback(
        self,
        *,
        callback_context: CallbackContext,
        llm_request: LlmRequest
    ) -> Optional[LlmResponse]:
        _text = _extract_user_text(llm_request=llm_request)
        if not _text:
            return None
        logger.info(
            f"[ModelArmorPlugin] Sanitizing user prompt: '{_text[:80]}...'"
        )

        try:
            req = modelarmor_v1.SanitizeUserPromptRequest(
                name=self.template_name,
                user_prompt_data=modelarmor_v1.DataItem(text=_text)
            )
            # 此處會透過 @property 觸發延遲載入，此時在雲端環境運作，可正常認證
            _result = self.client.sanitize_user_prompt(request=req)
            if self._blocked(result=_result):
                return self._block_response("很抱歉，基於安全考量，我無法處理此請求。請修改您的問題後再試一次。")
        except Exception as e:
            logger.error(f"[ModelArmorPlugin] user prompt screen error: {e}")
        return None

    async def after_model_callback(
        self,
        *,
        callback_context: CallbackContext,
        llm_response: LlmResponse
    ) -> Optional[LlmResponse]:
        _text = _extract_model_response(llm_response=llm_response)
        if not _text:
            return None
        logger.info(
            f"[ModelArmorPlugin] Sanitizing model response: '{_text[:80]}..."
        )
        try:
            req = modelarmor_v1.SanitizeModelResponseRequest(
                name=self.template_name,
                model_response_data=modelarmor_v1.DataItem(text=_text)
            )
            # 同樣會在這裡安全地動態取得 Client
            _result = self.client.sanitize_model_response(request=req)
            if self._blocked(result=_result):
                return self._block_response("很抱歉，我的回覆因安全考量被過濾，請換個方式詢問。")
        except Exception as e:
            logger.error(f"[ModelArmorPlugin] response screen error: {e}")
        return None
