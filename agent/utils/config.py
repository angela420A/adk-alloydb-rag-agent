import dataclasses
import os
from dataclasses import dataclass
from typing import Optional

from google.cloud import location


@dataclasses.dataclass(frozen=True)
class Models:
  root_agent_model: str = os.getenv('ROOT_MODEL', 'gemini-flash-latest')


@dataclasses.dataclass(frozen=True)
class ModelArmorConfig:
  template_id: Optional[str] = os.getenv('MODEL_ARMOR_TEMPLATE_ID')

  @property
  def enabled(self) -> bool:
    return bool(self.template_id)


MODELS = Models()
MODEL_ARMOR = ModelArmorConfig()
