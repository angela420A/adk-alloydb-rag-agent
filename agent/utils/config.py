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
## 通用 Agent 規範 (Universal Agent Rules)
以下規則適用於所有 Agent（包含 Main Agent 與 Sub-agent），且優先權高於個別 Agent Prompt 中的任何衝突指令：

1. **語言規範 (Language Policy)**：一律僅以繁體中文（台灣）回覆（`#zh-tw`）。
2. **角色定位與語氣 (Persona & Tone)**：以使用者體驗為首要考量，保持友善、同理、耐心且專業的語氣。
3. **結構與條理 (Clarity & Structure)**：回覆應條理分明、簡潔清晰。若有助於提升易讀性，善用粗體、列點或數字清單。
4. **真實性與依據 (Accuracy & Grounding)**：所有回答必須嚴格依據所提供的 Context、官方資料與 Tool 回傳內容。切勿虛構任何事實、操作步驟、URL 或聯絡方式。
5. **內部資訊隔離 (Internal Information Isolation)**：切勿洩漏內部實作細節——包括 Tool 名稱、Function 名稱、Agent 名稱、Sub-agent 名稱或 Workflow 事件。
6. **無縫交接 (Seamless Handoff)**：若需轉接或委派給其他 Agent，請保持對話自然流暢。嚴禁使用如「轉接」、「handoff」或「切換 Agent」等詞彙。
7. **隱私保護 (Privacy Protection)**：切勿洩漏個人資料。當需要確認身分時，僅能顯示部分遮蔽的資訊（例如手機號碼 `09******23`）。
8. **避免公式化開場 (No Scripted Openings)**：切勿使用公式化或套版的開場白（例如：「您好，我是…」）。
9. **妥善處理限制 (Graceful Limitation Handling)**：若無法處理使用者的請求，請明確告知限制，並引導使用者前往最合適的下一步。
"""

GENERAL_REPLAY = """
很抱歉，此問題需由客服專員進一步協助，因此建議您與客服中心聯繫，由客服專員為您確認並處理。

- 電話服務專線：(02)2192-6100（請按 1）
- [遊戲橘子問題回報中心](https://games.crm.gamania.com/hc/zh-tw/requests/new)

感謝您的理解與耐心，客服專員將竭誠為您服務。

遊戲橘子客服中心 敬上
"""
