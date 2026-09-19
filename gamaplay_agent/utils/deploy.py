import asyncio
from datetime import datetime
import importlib
import inspect
import json
import logging
import os
from pathlib import Path
import sys
from typing import Any
from zoneinfo import ZoneInfo
import click
import vertexai
from vertexai._genai import _agent_engines_utils
import yaml

logger = logging.getLogger(__name__)

from gamaplay_agent.utils.env import load_env

try:
    load_env()
except Exception as e:
    logging.warning(
        f"Could not load environment configuration via load_env(): {e}"
    )

# def _parse_key_value_pairs(kv_string: str | None) -> dict[str, str]:
#     result = {}
#     if not kv_string:
#         return result
#     for pair in kv_string.split(","):
#         pair = pair.strip()
#         if not pair:
#             continue
#         if "=" in pair:
#             key, val = pair.split("=", 1)
#             key = key.strip()
#             val = val.strip()
#             if key and val:
#                 result[key] = val
#             elif key:
#                 logging.warning(
#                     f"Skipping empty value for key '{key}' in key-value pairs."
#                 )
#         else:
#             logging.warning(f"Skipping malformed key-value pair: {pair}")
#     return result

# def _introspect_class_methods(entrypoint_module: str,
#                               entrypoint_object: str) -> list[dict[str,
#                                                                    Any]]:
#     """
#     【方案 B：動態自檢產生 class_methods (Dynamic Introspection)】
#     參考 Google `agents-cli` 的底層機制：
#     1. 在本地動態載入 entrypoint_module 中的 entrypoint_object。
#     2. 呼叫 _agent_engines_utils._get_registered_operations(agent=obj)。
#     3. 透過 _agent_engines_utils._generate_class_methods_spec_or_raise 自動產生 OpenAPI Schema。
#     4. 將生成的 spec 轉換成 dict 傳給 Vertex AI Agent Engine。
#     """
#     logging.info(
#         f"🔍 Introspecting agent class methods from {entrypoint_module}.{entrypoint_object}..."
#     )

#     # 確保當前目錄在 Python sys.path 中
#     if "." not in sys.path:
#         sys.path.insert(0, ".")

#     try:
#         module = importlib.import_module(entrypoint_module)
#         obj = getattr(module, entrypoint_object)

#         # 若物件為 Coroutine (非同步實例)，先予以執行解析
#         if inspect.iscoroutine(obj):
#             obj = asyncio.run(obj)

#         # 透過 Vertex AI 內建工具自動萃取已註冊的 operations
#         ops = _agent_engines_utils._get_registered_operations(agent=obj)
#         specs = _agent_engines_utils._generate_class_methods_spec_or_raise(
#             agent=obj,
#             operations=ops
#         )
#         class_methods = [_agent_engines_utils._to_dict(s) for s in specs]

#         logging.info(
#             f"✅ Successfully introspected {len(class_methods)} operations: "
#             f"{[m.get('name') for m in class_methods]}"
#         )
#         return class_methods

#     except Exception as e:
#         logging.error(f"Failed to introspect agent object: {e}")
#         raise click.ClickException(
#             f"Could not introspect agent {entrypoint_module}.{entrypoint_object}: {e}"
#         )


def _load_manifest_config(
    app_env: str | None = None,
    manifest_path: str | None = None,
) -> tuple[dict[str,
                Any],
           str | None]:
    """讀取對應環境的 manifest.yaml 取得專案靜態配置。

    優先搜尋順序:
      1. 明確指定的 manifest_path (例如 CLI 傳入 --manifest)
      2. manifests/agent-manifest.{app_env}.yaml (標準環境目錄)
      3. agent-manifest.{app_env}.yaml (根目錄環境檔案)
      4. manifests/agent-{app_env}-manifest.yaml (舊版格式相容)
      5. agents-cli-manifest.yaml (預設/相容舊檔名)
    """
    candidates = []
    if manifest_path:
        candidates.append(Path(manifest_path))
    else:
        env_name = app_env or os.environ.get("APP_ENV")
        if env_name:
            candidates.extend(
                [
                    Path(f"manifests/agent-manifest.{env_name}.yaml"),
                    Path(f"agent-manifest.{env_name}.yaml"),
                    Path(f"manifests/agent-{env_name}-manifest.yaml"),
                    Path(f"agent-{env_name}-manifest.yaml"),
                ]
            )
        candidates.append(Path("agents-cli-manifest.yaml"))

    for file_path in candidates:
        if file_path.exists():
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                    if isinstance(data, dict):
                        return data, str(file_path)
            except Exception as e:
                logging.warning(
                    f"Failed to read manifest file '{file_path}': {e}"
                )

    logging.warning(
        f"No manifest file found (searched: {[str(p) for p in candidates]})."
    )
    return {}, None


def _resolve_python_version(
    cli_version: str | None,
    manifest_version: str | None,
) -> str | None:
    """決定 Agent Runtime 使用的 Python 版本。

    優先順序:
      1. CLI 參數 (--python-version)
      2. 專案根目錄的 .python-version 檔案
      3. agents-cli-manifest.yaml 中的 python_version
    """
    if cli_version:
        v = cli_version.strip()
        parts = v.split(".")
        return f"{parts[0]}.{parts[1]}" if len(parts) >= 2 else v

    py_version_file = Path(".python-version")
    if py_version_file.exists():
        try:
            content = py_version_file.read_text(encoding="utf-8").strip()
            if content:
                parts = content.split(".")
                return f"{parts[0]}.{parts[1]}" if len(parts) >= 2 else content
        except Exception as e:
            logging.warning(f"Failed to read .python-version file: {e}")

    if manifest_version:
        parts = str(manifest_version).strip().split(".")
        return f"{parts[0]}.{parts[1]}" if len(parts) >= 2 else str(
            manifest_version
        ).strip()
    return None


def _parse_key_value_pairs(kv_string: str | None) -> dict[str, str]:
    """解析以逗號分隔的 KEY=VALUE 字串為字典。"""
    result = {}
    if not kv_string:
        return result
    for pair in kv_string.split(","):
        pair = pair.strip()
        if not pair:
            continue
        if "=" in pair:
            key, val = pair.split("=", 1)
            key, val = key.strip(), val.strip()
            if key and val:
                result[key] = val
        else:
            logging.warning(f"Skipping malformed key-value pair: {pair}")
    return result


def _parse_secrets(secrets_string: str | None) -> dict[str, dict[str, str]]:
    """解析 Secret Manager 密鑰規格 (ENV_VAR=SECRET_NAME 或 ENV_VAR=SECRET_NAME:VERSION)。"""
    raw = _parse_key_value_pairs(secrets_string)
    result = {}
    for key, spec in raw.items():
        if ":" not in spec:
            secret_id, version = spec, "latest"
        else:
            secret_id, _, version = spec.rpartition(":")
        result[key] = {"secret": secret_id, "version": version}
    return result


def _build_runtime_env_vars(
    set_env_vars: str | None,
    secrets: dict[str,
                  dict[str,
                       str]],
) -> dict[str,
          Any]:
    """組裝 Agent Engine 執行期的環境變數。"""
    env_vars: dict[str,
                   Any] = {
                       "GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY": "true",
                       "TZ": "Asia/Taipei",
                   }

    # 自動透傳常用環境變數
    passthrough_keys = [
        "APP_ENV",
        "PROJECT_NAME",
        "MODEL_ARMOR_TEMPLATE_ID",
        "LOGS_BUCKET_NAME",
        "TOOLBOX_URI",
        "ALLOYDB_DATABASE",
        "TZ",
        "OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT",
    ]
    for key in passthrough_keys:
        val = os.getenv(key)
        if val is not None and val != "":
            env_vars[key] = val

    custom_vars = _parse_key_value_pairs(set_env_vars)
    env_vars.update(custom_vars)
    env_vars.update(secrets)

    # 過濾空字串避免 API 報錯
    return {k: v for k, v in env_vars.items() if v is not None and v != ""}


def _introspect_class_methods(
    entrypoint_module: str,
    entrypoint_object: str,
) -> list[dict[str,
               Any]]:
    """動態自檢 Agent 實例以提取已註冊的 operations 及 OpenAPI Schema。"""
    logging.info(
        f"🔍 Introspecting agent class methods from {entrypoint_module}.{entrypoint_object}..."
    )

    if "." not in sys.path:
        sys.path.insert(0, ".")

    try:
        module = importlib.import_module(entrypoint_module)
        obj = getattr(module, entrypoint_object)

        if inspect.iscoroutine(obj):
            obj = asyncio.run(obj)

        ops = _agent_engines_utils._get_registered_operations(agent=obj)
        specs = _agent_engines_utils._generate_class_methods_spec_or_raise(
            agent=obj,
            operations=ops,
        )
        class_methods = [_agent_engines_utils._to_dict(s) for s in specs]

        logging.info(
            f"✅ Successfully introspected {len(class_methods)} operations: "
            f"{[m.get('name') for m in class_methods]}"
        )
        return class_methods

    except Exception as e:
        logging.error(f"Failed to introspect agent object: {e}")
        raise click.ClickException(
            f"Could not introspect agent {entrypoint_module}.{entrypoint_object}: {e}"
        )


def _write_deployment_metadata(
    remote_agent: Any,
    cfg: dict[str,
              Any],
    app_env: str | None = None,
    is_a2a: bool = False,
) -> Path:
    """Write deployment metadata to ./metadata/deployment_metadata.${APP_ENV}.json."""
    env_name = app_env or os.getenv("APP_ENV", "dev")
    output_dir = Path("metadata")
    output_file = output_dir / f"deployment_metadata.{env_name}.json"

    output_dir.mkdir(parents=True, exist_ok=True)

    agent_id = getattr(
        getattr(remote_agent,
                "api_resource",
                None),
        "name",
        str(remote_agent),
    )

    metadata = {
        "remote_agent_runtime_id":
            agent_id,
        "deployment_target":
            "agent_runtime",
        "environment":
            env_name,
        "display_name":
            cfg.get("display_name"),
        "service_account":
            cfg.get("service_account"),
        "agent_framework":
            cfg.get("agent_framework",
                    "google-adk"),
        "is_a2a":
            is_a2a,
        "deployment_timestamp":
            (datetime.now(ZoneInfo("Asia/Taipei")).isoformat()),
    }

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    logging.info(f"Deployment metadata written to {output_file}")
    return output_file


@click.command()
@click.option(
    "--project",
    default=None,
    envvar="GOOGLE_CLOUD_PROJECT",
    help="GCP Project ID (defaults to GOOGLE_CLOUD_PROJECT env var)",
)
@click.option(
    "--location",
    default=None,
    envvar="GOOGLE_CLOUD_LOCATION",
    help="GCP Region (defaults to GOOGLE_CLOUD_LOCATION or manifest region)",
)
@click.option(
    "--source-packages",
    multiple=True,
    default=None,
    help=
    "List of local source code directories (defaults to manifest agent_directory)",
)
@click.option(
    "--entrypoint-module",
    default=None,
    help="Python module path (e.g. app.agent_runtime_app)",
)
@click.option(
    "--entrypoint-object",
    default=None,
    help=
    "Variable name of the instantiated Agent within the module (e.g. agent_runtime)",
)
@click.option(
    "--requirements-file",
    default=None,
    help=
    "Path to requirements.txt (defaults to manifest or app/utils/.requirements.txt)",
)
@click.option(
    "--display-name",
    default=None,
    help="Display name for the agent engine (defaults to manifest 'name')",
)
@click.option(
    "--description",
    default=None,
    help="Description of the agent",
)
@click.option(
    "--set-env-vars",
    default=None,
    help=
    "Comma-separated KEY=VALUE environment variables to pass to the container",
)
# @click.option(
#     "--build-options",
#     default=None,
#     help=(
#         "JSON string for build options, e.g. "
#         "'{\"installation_scripts\": [\"scripts/install.sh\"]}'"
#     ),
# )
# @click.option(
#     "--identity-type",
#     default=None,
#     type=click.Choice(
#         ["SERVICE_ACCOUNT",
#          "AGENT_IDENTITY"],
#         case_sensitive=True
#     ),
#     help="Agent identity type for per-agent IAM access control.",
# )
@click.option(
    "--secrets",
    default=None,
    help=
    "Comma-separated ENV_VAR=SECRET_NAME or ENV_VAR=SECRET_NAME:VERSION for Secret Manager",
)
@click.option(
    "--service-account",
    default=None,
    envvar="AGENT_SERVICE_ACCOUNT",
    help="Service account email used by the agent runtime",
)
@click.option(
    "--min-instances",
    type=int,
    default=None,
    help="Minimum number of instances",
)
@click.option(
    "--max-instances",
    type=int,
    default=None,
    help="Maximum number of instances",
)
@click.option(
    "--cpu",
    default=None,
    help="CPU limit per container (default: 4)",
)
@click.option(
    "--memory",
    default=None,
    help="Memory limit per container (default: 8Gi)",
)
@click.option(
    "--container-concurrency",
    type=int,
    default=None,
    help="Max concurrent requests per container (default: 9)",
)
# @click.option(
#     "--encryption-spec",
#     default=None,
#     help=(
#         "JSON string for CMEK encryption spec, e.g. "
#         "'{\"kms_key_name\": \"projects/…/cryptoKeys/…\"}'"
#     ),
# )
@click.option(
    "--agent-framework",
    default="google-adk",
    help="The Agent Framework this project uses (default: google-adk)",
)
@click.option(
    "--is-a2a",
    is_flag=True,
    default=None,
    help="Whether this agent uses the Agent2Agent (A2A) protocol",
)
# @click.option(
#     "--labels",
#     default=None,
#     help="Comma-separated KEY=VALUE resource labels.",
# )
@click.option(
    "--psc-network-attachment",
    default=None,
    envvar="PSC_NETWORK_ATTACHMENT",
    help="PSC Network Attachment resource name",
)
@click.option(
    "--vpc-network",
    default=None,
    envvar="VPC_NETWORK_NAME",
    help="VPC network name for PSC DNS peering",
)
@click.option(
    "--dns-domain-model-armor",
    default=None,
    envvar="DNS_MODEL_ARMOR_DOMAIN_NAME",
    help="DNS domain name for Model Armor peering",
)
@click.option(
    "--dns-domain-run-app",
    default=None,
    envvar="DNS_RUN_APP_DOMAIN_NAME",
    help="DNS domain name for Cloud Run service peering",
)
@click.option(
    "--disable-psc",
    is_flag=True,
    default=False,
    help="Explicitly disable PSC network configuration",
)
@click.option(
    "--python-version",
    default=None,
    help=
    "Python version for Agent Runtime (e.g. 3.10, 3.11, 3.12, 3.13, 3.14). Defaults to .python-version file, then manifest.",
)
@click.option(
    "--manifest",
    default=None,
    help=
    "Custom path to manifest YAML file (defaults to manifests/agent-manifest.{APP_ENV}.yaml)",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help=
    "Validate configuration and class methods without deploying to Vertex AI",
)
def deploy(
    project: str | None,
    location: str | None,
    source_packages: tuple[str,
                           ...] | None,
    entrypoint_module: str | None,
    entrypoint_object: str | None,
    requirements_file: str | None,
    display_name: str | None,
    description: str | None,
    set_env_vars: str | None,
    secrets: str | None,
    service_account: str | None,
    min_instances: int | None,
    max_instances: int | None,
    cpu: str | None,
    memory: str | None,
    container_concurrency: int | None,
    agent_framework: str,
    is_a2a: bool | None,
    psc_network_attachment: str | None,
    vpc_network: str | None,
    dns_domain_model_armor: str | None,
    dns_domain_run_app: str | None,
    disable_psc: bool,
    python_version: str | None,
    manifest: str | None,
    dry_run: bool,
):
    # load env
    app_env = os.environ.get("APP_ENV")
    if not app_env:
        try:
            app_env = load_env()
        except Exception as e:
            raise click.ClickException(
                f"Missing required environment variable 'APP_ENV': {e}"
            )

    # load .yaml file
    manifest_data, manifest_source = _load_manifest_config(
        app_env=app_env,
        manifest_path=manifest,
    )

    manifest_name = manifest_data.get("name")
    project_name = os.getenv("PROJECT_NAME") or manifest_name or "agent"

    # 決定基本參數 (優先序: CLI 參數 > .env > YAML Manifest)
    project = project or os.getenv("GOOGLE_CLOUD_PROJECT")
    if not project:
        raise click.ClickException(
            f"Missing GCP Project ID! Set GOOGLE_CLOUD_PROJECT in .env.{app_env} or pass --project."
        )

    location = location or os.getenv("GOOGLE_CLOUD_LOCATION"
                                    ) or manifest_data.get("region")
    if not location:
        raise click.ClickException(
            f"Missing GCP Region / Location! Set GOOGLE_CLOUD_LOCATION in .env.{app_env} or pass --location."
        )

    display_name = display_name or manifest_name or project_name
    description = description or f"{display_name} Agent Engine ({app_env})"

    # Agent directory & Entrypoint
    manifest_dir = manifest_data.get("agent_directory", "app")
    if not source_packages:
        source_packages = (f"./{manifest_dir}",)

    manifest_ep = manifest_data.get("entrypoint", {})
    entrypoint_module = entrypoint_module or manifest_ep.get(
        "module",
        f"{manifest_dir}.agent_runtime_app"
    )
    entrypoint_object = entrypoint_object or manifest_ep.get(
        "object",
        "agent_runtime"
    )
    requirements_file = requirements_file or manifest_ep.get(
        "requirements_file",
        f"{manifest_dir}/utils/.requirements.txt"
    )

    # 解析 Python Version (CLI > .python-version > manifest > 系統預設)
    python_version = _resolve_python_version(
        cli_version=python_version,
        manifest_version=manifest_data.get("python_version"),
    )

    # 運算資源設定
    res_cfg = manifest_data.get("runtime_resources", {})
    cpu = cpu or res_cfg.get("cpu", "4")
    memory = memory or res_cfg.get("memory", "8Gi")
    container_concurrency = container_concurrency or res_cfg.get(
        "container_concurrency",
        9
    )
    min_instances = min_instances or res_cfg.get("min_instances", 1)
    max_instances = max_instances or res_cfg.get("max_instances", 10)

    # Service account & Identity type
    service_account = service_account or os.getenv("AGENT_SERVICE_ACCOUNT")
    identity_type = "SERVICE_ACCOUNT" if service_account and service_account != "None" else None

    # is_a2a (CLI > Manifest > False)
    if is_a2a is None:
        is_a2a = bool(manifest_data.get("is_a2a", False))

    # Secrets
    parsed_secrets = _parse_secrets(secrets)
    env_vars = _build_runtime_env_vars(set_env_vars, parsed_secrets)

    # Class methods
    class_methods = _introspect_class_methods(
        entrypoint_module=entrypoint_module,
        entrypoint_object=entrypoint_object,
    )

    # PSC & network & DNS
    psc_interface_config = None
    if not disable_psc and psc_network_attachment:
        dns_peering_configs = []
        if dns_domain_run_app and vpc_network:
            dns_peering_configs.append(
                {
                    "domain": dns_domain_run_app,
                    "target_project": project,
                    "target_network": vpc_network,
                }
            )
        if dns_domain_model_armor and vpc_network:
            dns_peering_configs.append(
                {
                    "domain": dns_domain_model_armor,
                    "target_project": project,
                    "target_network": vpc_network,
                }
            )
        psc_interface_config = {
            "network_attachment": psc_network_attachment,
            "dns_peering_configs": dns_peering_configs,
        }

    # Agent config
    config: dict[str,
                 Any] = {
                     "source_packages": list(source_packages),
                     "entrypoint_module": entrypoint_module,
                     "entrypoint_object": entrypoint_object,
                     "class_methods": class_methods,
                     "requirements_file": requirements_file,
                     "display_name": display_name,
                     "description": description,
                     "min_instances": min_instances,
                     "max_instances": max_instances,
                     "resource_limits": {
                         "cpu": cpu,
                         "memory": memory,
                     },
                     "container_concurrency": container_concurrency,
                     "agent_framework": agent_framework,
                 }

    if python_version:
        config["python_version"] = python_version
    if env_vars:
        config["env_vars"] = env_vars
    if identity_type:
        config["identity_type"] = identity_type
    if service_account:
        config["service_account"] = service_account
    if psc_interface_config:
        config["psc_interface_config"] = psc_interface_config

    print("\n📦 Deployment Configuration Summary:")
    print(f"  • Environment:      {app_env}")
    print(f"  • Manifest File:    {manifest_source or 'None'}")
    print(f"  • Project:          {project}")
    print(f"  • Location:         {location}")
    print(f"  • Display Name:     {display_name}")
    print(
        f"  • Python Version:   {python_version or f'{sys.version_info.major}.{sys.version_info.minor} (system default)'}"
    )
    print(f"  • Service Account:  {service_account or 'None'}")
    print(f"  • A2A Protocol:     {is_a2a}")
    print(f"  • CPU / Memory:     {cpu} / {memory}")
    print(f"  • Concurrency:      {container_concurrency}")
    print(f"  • Instances:        {min_instances} min / {max_instances} max")
    print(
        f"  • PSC Status:       {'Enabled' if psc_interface_config else 'Disabled'}"
    )
    print(f"  • Runtime Env Vars: {list(env_vars.keys())}")

    if dry_run:
        print(
            "\n🔍 [Dry Run] Configuration validation succeeded. Deployment skipped."
        )
        print(json.dumps(config, indent=2, default=str))
        return

    # Check if same display name agent has existed or not: update / create
    client = vertexai.Client(project=project, location=location)

    print(
        f"\n🔍 Checking for existing Agent Engine with display name '{display_name}'..."
    )
    existing_agents = list(client.agent_engines.list())
    matching_agents = [
        agent for agent in existing_agents
        if agent.api_resource.display_name == display_name
    ]

    if matching_agents:
        target_agent = matching_agents[0]
        print(
            f"🔄 Found existing Agent Engine: {target_agent.api_resource.name}"
        )
        print(f"🚀 Updating Agent Engine ({display_name})...")
        remote_agent = client.agent_engines.update(
            name=target_agent.api_resource.name,
            config=config,
        )
    else:
        print(f"🚀 Creating new Agent Engine ({display_name})...")
        remote_agent = client.agent_engines.create(config=config)

    print(
        f"\n✅ Deployment complete! Agent Resource ID: {remote_agent.api_resource.name}"
    )

    _write_deployment_metadata(
        remote_agent=remote_agent,
        cfg=config,
        app_env=app_env,
        is_a2a=is_a2a,
    )


if __name__ == "__main__":
    deploy()
