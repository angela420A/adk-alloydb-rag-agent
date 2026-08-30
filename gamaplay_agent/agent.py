import uuid
import asyncio
from google.adk import tools
import logging
import os
import logging
import asyncio

from google.adk.apps import App
from google.genai import types
from google.adk.agents.llm_agent import Agent
from google.adk.runners import InMemoryRunner, Runner
# from google.adk.tools.toolbox_toolset import ToolboxToolset
from toolbox_adk import CredentialStrategy, ToolboxToolset

from gamaplay_agent.utils.env import load_env

load_env()

from gamaplay_agent.utils import config
from gamaplay_agent.plugins.model_armor import ModelArmorPlugin
# from gamaplay_agent.guards.model_armor_guard import create_guard

from gamaplay_agent.prompt import SYSTEM_INSTRUCTION

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s[%(name)s] [%(levelname)s]: %(message)s'
)

TOOLBOX_URI = os.getenv('TOOLBOX_URI', '')

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
    os.environ.setdefault("GOOGLE_CLOUD_LOCATION", "asia-southeast1")
    os.environ.setdefault("GOOGLE_GENAI_USE_VERTEXAI", "True")


def create_agent() -> Agent:
    _init_agent_platform()

    return Agent(
        name='gamaplay_agent',
        model=config.MODELS.root_agent_model,
        instruction=SYSTEM_INSTRUCTION,
        tools=[toolset]
    )


root_agent = create_agent()

app = App(
    name='gamaplay_agent',
    root_agent=root_agent,
    plugins=[ModelArmorPlugin()]
)
