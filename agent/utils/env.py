"""Environment configuration and validation utility for Agent."""

import logging
import os
from pathlib import Path

from dotenv import load_dotenv

logger = logging.getLogger(__name__)

ALLOWED_ENVS = {"dev", "staging", "prod"}
_ENV_LOADED = False


def load_env(override: bool = False) -> str:
    """Load and validate the environment configuration based on APP_ENV.

    Args:
        override: Whether to force reloading the environment file even if
            already loaded.

    Returns:
        The validated APP_ENV string.

    Raises:
        RuntimeError: If APP_ENV is not set.
        ValueError: If APP_ENV is not one of the allowed environments ('dev',
            'staging', 'prod').
    """
    global _ENV_LOADED
    if _ENV_LOADED and not override:
        return os.environ.get("APP_ENV", "")

    app_env = os.environ.get("APP_ENV")
    if not app_env:
        raise RuntimeError(
            "❌ [CRITICAL] 'APP_ENV' environment variable is not set! "
            "Please set APP_ENV (e.g. export APP_ENV=dev) before starting "
            "the application."
        )

    if app_env not in ALLOWED_ENVS:
        raise ValueError(
            f"❌ [CRITICAL] Invalid APP_ENV='{app_env}'. "
            f"Allowed values are: {sorted(ALLOWED_ENVS)}"
        )

    env_file = f".env.{app_env}"
    env_path = Path(env_file)

    if env_path.exists():
        load_dotenv(dotenv_path=env_path, override=override)
        logger.info(f"Loaded environment variables from '{env_file}'.")
    else:
        logger.info(
            f"Environment file '{env_file}' not found; "
            "using existing system environment variables."
        )

    _ENV_LOADED = True
    return app_env


# Alias for backward compatibility or alternate naming
load_env_value = load_env
