from google.cloud import location
from dataclasses import dataclass
import os
import dataclasses
from typing import Optional


@dataclasses.dataclass(frozen=True)
class Models:
    # gemini-3.5-flash, gemini-flash-latest not support region
    root_agent_model: str = os.getenv('ROOT_MODEL', 'gemini-2.5-flash')


@dataclasses.dataclass(frozen=True)
class ModelArmorConfig:
    template_id: Optional[str] = os.getenv('MODEL_ARMOR_TEMPLATE_ID')

    @property
    def enabled(self) -> bool:
        return bool(self.template_id)


@dataclasses.dataclass
class UserData:
    MainAccountName: Optional[str] = None
    OpenID: Optional[str] = None
    GameName: Optional[str] = None
    GameServiceCode: Optional[str] = None
    MainAccountMobile: Optional[str] = None
    GamaPassNo: Optional[str] = None
    IsGamaPassAccount: Optional[bool] = None


MODELS = Models()
MODEL_ARMOR = ModelArmorConfig()

SYSTEM_IMPORTANT = """
## Universal Agent Rules
The following rules apply to every agent and take precedence over any conflicting instruction in an agent-specific prompt:

1. **Language Policy**: Always respond in Traditional Chinese (Taiwan) only, `#zh-tw`.
2. **Persona & Tone**: Maintain a friendly, empathetic, patient, and professional tone with user experience as the top priority.
3. **Clarity & Structure**: Keep responses clear, concise, and well-structured. Use bold text, bullet points, or numbered lists when they improve readability.
4. **Accuracy & Grounding**: Base all answers strictly on provided context, official information, and tool outputs. Do not fabricate facts, procedures, URLs, or contact details.
5. **Internal Information Isolation**: Never reveal internal implementation details — including tool names, function names, agent names, sub-agent names, or workflow events.
6. **Seamless Handoff**: If routing or delegation to another agent is required, keep the conversation natural. Never use terms such as "transfer", "handoff", or "agent switch".
7. **Privacy Protection**: Never expose personal data. When identity confirmation is needed, display only partially masked information (e.g., phone number `09******23`).
8. **No Scripted Openings**: Do not use formulaic opening lines (e.g., "您好，我是…").
9. **Graceful Limitation Handling**: If a request cannot be resolved, clearly acknowledge the limitation and guide the user toward the most appropriate next step.
"""

GENERAL_REPLAY = """
很抱歉，此問題需由客服專員進一步協助，因此建議您與客服中心聯繫，由客服專員為您確認並處理。

電話服務專線：(02)2192-6100（請按 1）
遊戲橘子問題回報中心：https://games.crm.gamania.com/hc/zh-tw/requests/new

感謝您的理解與耐心，客服專員將竭誠為您服務。

遊戲橘子客服中心 敬上
"""
