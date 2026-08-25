import asyncio
import importlib
import inspect
import json
import logging
import os
import sys
from typing import Any
import click
import vertexai
from vertexai._genai import _agent_engines_utils

logger = logging.getLogger(__name__)

from gamaplay_agent.utils.env import load_env

try:
    load_env()
except Exception as e:
    logging.warning(
        f"Could not load environment configuration via load_env(): {e}"
    )


def _parse_key_value_pairs(kv_string: str | None) -> dict[str, str]:
    result = {}
    if not kv_string:
        return result
    for pair in kv_string.split(","):
        pair = pair.strip()
        if not pair:
            continue
        if "=" in pair:
            key, val = pair.split("=", 1)
            key = key.strip()
            val = val.strip()
            if key and val:
                result[key] = val
            elif key:
                logging.warning(
                    f"Skipping empty value for key '{key}' in key-value pairs."
                )
        else:
            logging.warning(f"Skipping malformed key-value pair: {pair}")
    return result


def _introspect_class_methods(entrypoint_module: str,
                              entrypoint_object: str) -> list[dict[str,
                                                                   Any]]:
    """
    【方案 B：動態自檢產生 class_methods (Dynamic Introspection)】
    參考 Google `agents-cli` 的底層機制：
    1. 在本地動態載入 entrypoint_module 中的 entrypoint_object。
    2. 呼叫 _agent_engines_utils._get_registered_operations(agent=obj)。
    3. 透過 _agent_engines_utils._generate_class_methods_spec_or_raise 自動產生 OpenAPI Schema。
    4. 將生成的 spec 轉換成 dict 傳給 Vertex AI Agent Engine。
    """
    logging.info(
        f"🔍 Introspecting agent class methods from {entrypoint_module}.{entrypoint_object}..."
    )

    # 確保當前目錄在 Python sys.path 中
    if "." not in sys.path:
        sys.path.insert(0, ".")

    try:
        module = importlib.import_module(entrypoint_module)
        obj = getattr(module, entrypoint_object)

        # 若物件為 Coroutine (非同步實例)，先予以執行解析
        if inspect.iscoroutine(obj):
            obj = asyncio.run(obj)

        # 透過 Vertex AI 內建工具自動萃取已註冊的 operations
        ops = _agent_engines_utils._get_registered_operations(agent=obj)
        specs = _agent_engines_utils._generate_class_methods_spec_or_raise(
            agent=obj,
            operations=ops
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


@click.command()
@click.option(
    "--project",
    default=None,
    envvar="GOOGLE_CLOUD_PROJECT",
    help=
    "GCP project ID (defaults to GOOGLE_CLOUD_PROJECT env var or application default credentials)",
)
@click.option(
    "--location",
    default=None,
    envvar="GOOGLE_CLOUD_LOCATION",
    help="GCP region (defaults to GOOGLE_CLOUD_LOCATION env var)",
)
# -------------------------------------------------------------
# 【#from-source-files 新增 / 調整的選項】
# -------------------------------------------------------------
@click.option(
    "--source-packages",
    multiple=True,
    default=["./gamaplay_agent"],
    help=(
        "[Source files mode] List of local source code directories "
        "(replaces legacy extra_packages, within 8MB)"
    ),
)
@click.option(
    "--entrypoint-module",
    default="gamaplay_agent.agent_runtime_app",
    help=(
        "[Source files mode] Python module path (i.e. file path without .py) "
        "e.g. gamaplay_agent.agent_runtime_app"
    ),
)
@click.option(
    "--entrypoint-object",
    default="agent_runtime",
    help=(
        "[Source files mode] Variable name of the instantiated Agent within the module. "
        "e.g. agent_runtime"
    ),
)
@click.option(
    "--requirements-file",
    default="gamaplay_agent/utils/.requirements.txt",
    help="Path to requirements.txt",
)
# -------------------------------------------------------------
# 【通用設定】
# -------------------------------------------------------------
@click.option(
    "--display-name",
    default=None,
    envvar="AGENT_DISPLAY_NAME",
    help=
    "Display name for the agent engine (defaults to gamaplay-agent-{APP_ENV}).",
)
@click.option(
    "--description",
    default="Gama Play App Customer Support Agent (Auto-Introspected)",
    help="Description of the agent.",
)
@click.option(
    "--set-env-vars",
    default=None,
    help=
    "Comma-separated KEY=VALUE environment variables to pass to the agent runtime container.",
)
@click.option(
    "--build-options",
    default=None,
    help=(
        "JSON string for build options, e.g. "
        "'{\"installation_scripts\": [\"scripts/install.sh\"]}'"
    ),
)
@click.option(
    "--identity-type",
    default=None,
    type=click.Choice(
        ["SERVICE_ACCOUNT",
         "AGENT_IDENTITY"],
        case_sensitive=True
    ),
    help="Agent identity type for per-agent IAM access control.",
)
@click.option(
    "--service-account",
    default=None,
    envvar="AGENT_SERVICE_ACCOUNT",
    help=
    "Service account email used by the agent at runtime (defaults to AGENT_SERVICE_ACCOUNT env var).",
)
@click.option(
    "--min-instances",
    type=int,
    default=1,
    help="Minimum number of instances (default: 1).",
)
@click.option(
    "--max-instances",
    type=int,
    default=10,
    help="Maximum number of instances (default: 10).",
)
@click.option(
    "--cpu",
    default="4",
    help="CPU limit per container (default: 4).",
)
@click.option(
    "--memory",
    default="8Gi",
    help="Memory limit per container (default: 8Gi).",
)
@click.option(
    "--container-concurrency",
    type=int,
    default=9,
    help="Max concurrent requests per container (default: 9).",
)
@click.option(
    "--encryption-spec",
    default=None,
    help=(
        "JSON string for CMEK encryption spec, e.g. "
        "'{\"kms_key_name\": \"projects/…/cryptoKeys/…\"}'"
    ),
)
@click.option(
    "--agent-framework",
    default="google-adk",
    help="The Agent Framework this project uses.",
)
@click.option(
    "--labels",
    default=None,
    help="Comma-separated KEY=VALUE resource labels.",
)
# -------------------------------------------------------------
# 【網路與 PSC 設定】
# -------------------------------------------------------------
@click.option(
    "--vpc-network",
    default=None,
    envvar="VPC_NETWORK_NAME",
    help=
    "VPC network name for PSC DNS peering (defaults to VPC_NETWORK_NAME env var).",
)
@click.option(
    "--psc-network-attachment",
    default=None,
    envvar="PSC_NETWORK_ATTACHMENT",
    help=
    "Resource name of the PSC network attachment (defaults to PSC_NETWORK_ATTACHMENT env var).",
)
@click.option(
    "--dns-domain-model-armor",
    default=None,
    envvar="DNS_MODEL_ARMOR_DOMAIN_NAME",
    help=
    "DNS domain name for Model Armor service peering (defaults to DNS_MODEL_ARMOR_DOMAIN_NAME env var).",
)
@click.option(
    "--dns-domain-run-app",
    default=None,
    envvar="DNS_RUN_APP_DOMAIN_NAME",
    help=
    "DNS domain name for Cloud Run service peering (defaults to DNS_RUN_APP_DOMAIN_NAME env var).",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help=
    "Validate configuration and class methods without deploying to Agent Engine.",
)
def deploy_to_agent_engine(
    project: str | None,
    location: str | None,
    source_packages: tuple[str,
                           ...],
    entrypoint_module: str,
    entrypoint_object: str,
    requirements_file: str,
    display_name: str | None,
    description: str,
    set_env_vars: str | None,
    build_options: str | None,
    identity_type: str | None,
    service_account: str | None,
    min_instances: int,
    max_instances: int,
    cpu: str,
    memory: str,
    container_concurrency: int,
    encryption_spec: str | None,
    agent_framework: str,
    labels: str | None,
    vpc_network: str | None,
    psc_network_attachment: str | None,
    dns_domain_model_armor: str | None,
    dns_domain_run_app: str | None,
    dry_run: bool,
):
    app_env = os.getenv("APP_ENV", "dev")
    project = project or os.getenv("GOOGLE_CLOUD_PROJECT")
    location = location or os.getenv("GOOGLE_CLOUD_LOCATION")
    display_name = display_name or (
        f"gamaplay-agent-{app_env}" if app_env else "gamaplay-agent"
    )

    # 處理 Service Account 與 Identity Type
    if service_account and service_account != "None":
        if not identity_type:
            identity_type = "SERVICE_ACCOUNT"
    else:
        service_account = None

    # 彙整環境變數 (僅傳遞 MODEL_ARMOR_TEMPLATE_ID, APP_ENV, TOOLBOX_URI 與 LOGS_BUCKET_NAME 給 Agent Runtime)
    runtime_env_keys = [
        "APP_ENV",
        "MODEL_ARMOR_TEMPLATE_ID",
        "LOGS_BUCKET_NAME",
        "TOOLBOX_URI"
    ]
    env_vars: dict[str, str] = {}
    for key in runtime_env_keys:
        val = os.getenv(key)
        if val is not None and val != "":
            env_vars[key] = val

    custom_env_vars = _parse_key_value_pairs(set_env_vars)
    env_vars.update(custom_env_vars)

    # 確保不會傳入空字串值的環境變數，避免 Vertex AI Agent Engine 回傳 400 錯誤
    env_vars = {k: v for k, v in env_vars.items() if v is not None and v != ""}

    labels_dict: dict[str, str] | None = _parse_key_value_pairs(labels) or None
    build_options_dict: dict | None = (
        json.loads(build_options) if build_options else None
    )
    encryption_spec_dict: dict | None = (
        json.loads(encryption_spec) if encryption_spec else None
    )

    # -------------------------------------------------------------------------
    # 【方案 B：使用 agents-cli 方式動態自動產生 class_methods】
    # -------------------------------------------------------------------------
    class_methods = _introspect_class_methods(
        entrypoint_module=entrypoint_module,
        entrypoint_object=entrypoint_object,
    )
    print(
        f"\n📋 Dynamically Generated Class Methods ({len(class_methods)} total):"
    )
    for method in class_methods:
        print(
            f"  - {method.get('name')} (api_mode: '{method.get('api_mode')}')"
        )

    # -------------------------------------------------------------------------
    # 【網路與 PSC 設定 (Private Service Connect)】
    # -------------------------------------------------------------------------
    psc_interface_config = None
    if psc_network_attachment:
        missing_psc_vars = []
        if not vpc_network:
            missing_psc_vars.append("VPC_NETWORK_NAME (--vpc-network)")
        if not dns_domain_model_armor and not dns_domain_run_app:
            missing_psc_vars.append(
                "DNS domain names (--dns-domain-run-app or --dns-domain-model-armor)"
            )

        if missing_psc_vars:
            raise click.ClickException(
                f"PSC configuration is incomplete. Missing: {', '.join(missing_psc_vars)}"
            )

        dns_peering_configs = []
        if dns_domain_run_app:
            dns_peering_configs.append(
                {
                    "domain": dns_domain_run_app,
                    "target_project": project,
                    "target_network": vpc_network,
                }
            )
        if dns_domain_model_armor:
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

    # -------------------------------------------------------------------------
    # 【組裝 Agent Engine 設定】
    # -------------------------------------------------------------------------
    config: dict[str,
                 Any] = {
                     # 來源檔案模式必填欄位
                     "source_packages": list(source_packages),
                     "entrypoint_module": entrypoint_module,
                     "entrypoint_object": entrypoint_object,
                     "class_methods": class_methods,
                     "requirements_file": requirements_file,
                     # 通用設定
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

    if env_vars:
        config["env_vars"] = env_vars
    if labels_dict:
        config["labels"] = labels_dict
    if build_options_dict:
        config["build_options"] = build_options_dict
    if identity_type:
        config["identity_type"] = identity_type
    if service_account:
        config["service_account"] = service_account
    if encryption_spec_dict:
        config["encryption_spec"] = encryption_spec_dict
    if psc_interface_config:
        config["psc_interface_config"] = psc_interface_config

    print("\n📦 Deployment Configuration Summary:")
    print(f"  • Environment:      {app_env}")
    print(f"  • Project:          {project}")
    print(f"  • Location:         {location}")
    print(f"  • Display Name:     {display_name}")
    print(f"  • Service Account:  {service_account or 'None'}")
    print(f"  • Identity Type:    {identity_type or 'None'}")
    print(f"  • CPU / Memory:     {cpu} / {memory}")
    print(f"  • Concurrency:      {container_concurrency}")
    print(f"  • Instances:        {min_instances} min / {max_instances} max")
    print(
        f"  • PSC Attachment:   {psc_network_attachment or 'None (Disabled)'}"
    )
    print(f"  • Runtime Env Vars: {list(env_vars.keys())}")

    if dry_run:
        print("\n🔍 [Dry Run] Config validation succeeded. Deployment skipped.")
        print(json.dumps(config, indent=2, default=str))
        return

    # -------------------------------------------------------------------------
    # 【#from-source-files 部署】
    # -------------------------------------------------------------------------
    print(f"\n🚀 Creating Agent Engine from source files ({display_name})...")
    client = vertexai.Client(project=project, location=location)
    remote_agent = client.agent_engines.create(config=config)

    print(
        f"\n✅ Deployment complete! Agent Resource ID: {remote_agent.api_resource.name}"
    )


if __name__ == "__main__":
    deploy_to_agent_engine()
