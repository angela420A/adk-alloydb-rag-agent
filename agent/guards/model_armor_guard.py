import os
import logging
from typing import Optional

from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmRequest, LlmResponse
from google.api_core.client_options import ClientOptions
from google.cloud import modelarmor_v1
from google.genai import types

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
        logger.error(f"[ModelArmorGuard] Error extracting user text: {e}")
    return ""


def _extract_model_response(llm_response: LlmResponse) -> str:
    try:
        if llm_response.content and llm_response.content.parts:
            for part in llm_response.content.parts:
                if hasattr(part, "text") and part.text:
                    return part.text
    except Exception as e:
        logger.error(f"[ModelArmorGuard] Error extracting model text: {e}")
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


class NoGuard:

    def before_model_callback(
        self,
        callback_context: CallbackContext,
        llm_request: LlmRequest
    ) -> Optional[LlmResponse]:
        return None

    def after_model_callback(
        self,
        callback_context: CallbackContext,
        llm_response: LlmResponse
    ) -> Optional[LlmResponse]:
        return None


class ModelArmorGuard:

    def __init__(self, project_id: str, template_id: str, location: str):
        self.project_id = project_id
        self.template_id = template_id
        self.location = location
        self.template_name = f"projects/{self.project_id}/locations/{self.location}/templates/{self.template_id}",

        self.client = modelarmor_v1.ModelArmorClient(
            transport="rest",
            client_options=ClientOptions(
                api_endpoint=f"modelarmor.{self.location}.rep.googleapis.com"
            ),
        )

        logger.info(
            f"[ModelArmorGuard] Initialized with template: {self.template_id}"
        )

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

    def before_model_callback(
        self,
        callback_context: CallbackContext,
        llm_request: LlmRequest
    ) -> Optional[LlmResponse]:
        _text = _extract_user_text(llm_request=llm_request)
        if not _text:
            return None
        logger.info(
            f"[ModelArmorGuard] Sanitizing user prompt: '{_text[:80]}...'"
        )

        try:
            req = modelarmor_v1.SanitizeUserPromptRequest(
                name=self.template_name,
                user_prompt_data=modelarmor_v1.DataItem(text=_text)
            )
            _result = self.client.sanitize_user_prompt(request=req)
            if self._blocked(result=_result):
                return self._block_response("很抱歉，基於安全考量，我無法處理此請求。請修改您的問題後再試一次。")
        except Exception as e:
            logger.error(f"[ModelArmorGuard] user prompt screen error: {e}")
        return None

    def after_model_callback(
        self,
        callback_context: CallbackContext,
        llm_response: LlmResponse
    ) -> Optional[LlmResponse]:
        _text = _extract_model_response(llm_response=llm_response)
        if not _text:
            return None
        logger.into(
            f"[ModelArmorGuard] Sanitizing model response: '{_text[:80]}..."
        )
        try:
            req = modelarmor_v1.SanitizeModelResponseRequest(
                name=self.template_name,
                model_response_data=modelarmor_v1.DataItem(text=_text)
            )
            _result = self.client.sanitize_model_response(request=req)
            if self._blocked(result=_result):
                return self._block_response("很抱歉，我的回覆因安全考量被過濾，請換個方式詢問。")
        except Exception as e:
            logger.error(f"[ModelArmorGuard] response screen error: {e}")
        return None


_guard_instance: Optional[ModelArmorGuard] = None


def create_guard():
    if _guard_instance is not None:
        return _guard_instance

    project_id = os.getenv('GOOGLE_CLOUD_PROJECT', None)
    location = os.getenv('GOOGLE_CLOUD_LOCATION', None)
    template_id = os.getenv('MODEL_ARMOR_TEMPLATE_ID', None)

    if not project_id or not location or not template_id:
        logger.error(".env file is not set")
        return NoGuard

    if config.MODEL_ARMOR.enabled:
        try:
            _guard_instance = ModelArmorGuard(
                project_id=project_id,
                template_id=template_id,
                location=location
            )
            return _guard_instance
        except Exception as e:
            logger.error(
                f'[ModelArmorGuard] ❌ init failed: {e}. Using no-op guard.'
            )
    return NoGuard
