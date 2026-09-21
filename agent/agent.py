import asyncio
import logging
import os
import uuid

from google.adk import tools
from google.adk.agents.llm_agent import Agent
from google.adk.apps import App
from google.adk.runners import InMemoryRunner, Runner
from google.genai import types

# from google.adk.tools.toolbox_toolset import ToolboxToolset
from toolbox_adk import CredentialStrategy, ToolboxToolset

from agent.utils.env import load_env

load_env()

from agent.plugins.model_armor import ModelArmorPlugin
from agent.prompt import SYSTEM_INSTRUCTION
from agent.utils import config

# from agent.guards.model_armor_guard import create_guard

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s[%(name)s] [%(levelname)s]: %(message)s'
)

TOOLBOX_URI = os.getenv('TOOLBOX_URI', '')
# TOOLBOX_URI = "http://127.0.0.1:7000/"

toolset = ToolboxToolset(
    server_url=TOOLBOX_URI,
    credentials=CredentialStrategy.workload_identity(
        target_audience=TOOLBOX_URI
    ),
)


def _init_agent_platform() -> None:
  try:
    import google.auth

    _, project_id = google.auth.default()
    if project_id:
      os.environ.setdefault('GOOGLE_CLOUD_PROJECT', project_id)
    else:
      logging.warning(
          "Could not determine the Google Cloud project. Set the GOOGLE_CLOUD_PROJECT environment variable manually."
      )
  except Exception as e:
    logging.warning(f'Failed to initialize GCP: {e}')
  os.environ.setdefault("GOOGLE_CLOUD_LOCATION", "us-central1")
  os.environ.setdefault("GOOGLE_GENAI_USE_VERTEXAI", "True")


def create_agent() -> Agent:
  _init_agent_platform()

  return Agent(
      name='agentic-agent',
      model=config.MODELS.root_agent_model,
      instruction=SYSTEM_INSTRUCTION,
      tools=[toolset]
  )


root_agent = create_agent()

app = App(
    name='agentic-agent', root_agent=root_agent, plugins=[ModelArmorPlugin()]
)
