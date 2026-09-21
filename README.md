# Agentic Agent

An AI customer support agent platform built with:

- **Google Agent Development Kit (ADK)**
- **Google Cloud Vertex AI Agent Runtime**
- **AlloyDB** (pgvector + hybrid search)
- **Model Context Protocol (MCP) Toolbox**
- **Model Armor** security guardrails

This repository is intended as a reusable reference you can clone, configure for your own GCP projects, and extend.

---

## Architecture Overview

![Agentic Agent System Design](images/Agentic-Agent-System-Design.drawio.png)

- **Agent Framework** ([`agent/`](agent)): Built on Google ADK (`google-adk`), wrapped in `AdkApp` for Vertex AI Reasoning Engine / Agent Runtime deployment.
- **Knowledge Retrieval**: Knowledge base articles stored in AlloyDB with multi-lingual embeddings (`text-multilingual-embedding-002`) and ScaNN vector indexing.
- **Tool Protocol**: Database queries orchestrated via Model Context Protocol (MCP) Toolbox, typically hosted on Cloud Run.
- **Security & Guardrails**: Integrated [`ModelArmorPlugin`](agent/plugins/model_armor.py) for prompt sanitization, jailbreak prevention, and response verification.
- **Infrastructure as Code** ([`deployment/`](deployment)): Automated Terraform modules for multi-environment (`dev`, `staging`, `prod`) provisioning.

---

## Getting Started

### Prerequisites

- **Python**: `>= 3.13`
- **Package Manager**: [`uv`](https://docs.astral.sh/uv/)
- **Google Cloud SDK**: [`gcloud`](https://cloud.google.com/sdk/docs/install) configured with Application Default Credentials:

  ```bash
  gcloud auth application-default login
  ```

- **(Optional, for infrastructure)** Terraform, and `psql` if you will bootstrap AlloyDB manually

### Installation

Clone the repository and install dependencies with `uv`:

```bash
git clone <YOUR_FORK_OR_REPO_URL>
cd adk-alloydb-rag-agent
uv sync
```

---

## Environment Configuration

> [!IMPORTANT]
> **Always set `APP_ENV` before running application commands or `Makefile` targets.**
>
> ```bash
> export APP_ENV=dev          # Options: dev, staging, prod
> ```
>
> The application uses **fail-fast validation**: if `APP_ENV` is missing or invalid, execution stops immediately to avoid unintended cross-environment operations.

### Environment File Setup

Copy the template to an environment-specific file and fill in the required values:

```bash
cp .env.example .env.dev
```

Repeat for other environments as needed (for example `.env.staging`, `.env.prod`).

### Key Environment Variables

| Variable | Description | Example / Placeholder |
| :--- | :--- | :--- |
| `ROOT_MODEL` | Gemini LLM model identifier | `gemini-flash-latest` |
| `GOOGLE_CLOUD_PROJECT` | Target GCP project ID | `<YOUR_GCP_PROJECT_ID>` |
| `GOOGLE_CLOUD_LOCATION` | Target GCP region | `<YOUR_GCP_REGION>` |
| `GOOGLE_CLOUD_LOCATION_ZONE` | Target GCP zone (for compute / bastion workflows) | `<YOUR_GCP_ZONE>` |
| `GOOGLE_GENAI_USE_VERTEXAI` | Use Vertex AI for GenAI APIs | `true` |
| `MODEL_ARMOR_TEMPLATE_ID` | Model Armor template ID | `<YOUR_MODEL_ARMOR_TEMPLATE_ID>` |
| `TF_VAR_alloydb_password` | AlloyDB password passed to Terraform (`TF_VAR_*`) | `<YOUR_SECURE_PASSWORD>` |
| `ALLOYDB_DATABASE` | Target AlloyDB database name | `<YOUR_ALLOYDB_DATABASE_NAME>` |
| `TOOLBOX_URI` | Cloud Run MCP Toolbox service endpoint | `https://<YOUR_TOOLBOX_SERVICE_URI>` |
| `AGENT_SERVICE_ACCOUNT` | Service account email for Agent Runtime | `<YOUR_AGENT_SERVICE_ACCOUNT_EMAIL>` |
| `LOGS_BUCKET_NAME` | GCS bucket for runtime telemetry logs | `<YOUR_LOGS_BUCKET_NAME>` |
| `OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT` | OpenTelemetry GenAI content capture mode | `NO_CONTENT` |
| `VPC_NETWORK_NAME` | VPC network name used by the runtime | `<YOUR_VPC_NETWORK_NAME>` |
| `PSC_NETWORK_ATTACHMENT` | Private Service Connect network attachment | `projects/<PROJECT_ID>/regions/<REGION>/networkAttachments/<ATTACHMENT_NAME>` |
| `DNS_MODEL_ARMOR_DOMAIN_NAME` | Private DNS domain for Model Armor | `<YOUR_MODEL_ARMOR_DNS_DOMAIN>` |
| `DNS_RUN_APP_DOMAIN_NAME` | Private DNS domain for Cloud Run app access | `<YOUR_RUN_APP_DNS_DOMAIN>` |

See [`.env.example`](.env.example) for the full template.

---

## Makefile Commands

All Makefile targets use the active `APP_ENV` configuration (and the matching `.env.${APP_ENV}` file).

### 1. Verification

Verify that environment variables and project configuration load correctly:

```bash
export APP_ENV=dev
make verify-env
```

### 2. Local Agent Development (ADK Web UI)

Run the agent interactively with the ADK local web console:

```bash
export APP_ENV=dev
make run-agent
```

### 3. Local MCP Toolbox for Databases

Download and run the MCP Toolbox locally for testing database tools.

> **Note:** `make toolbox-dw` downloads the **macOS ARM64** binary (`darwin/arm64`) at toolbox version `v1.9.0`. For Linux, Windows, or another architecture, download the matching asset from the [MCP Toolbox releases](https://github.com/googleapis/mcp-toolbox/releases) (or the GCS distribution referenced in the `Makefile`) and adjust the target as needed.

- **Download Toolbox binary** (macOS ARM64):

  ```bash
  make toolbox-dw
  ```

- **Run Toolbox CLI**:

  ```bash
  make toolbox
  ```

- **Run Toolbox Web UI**:

  ```bash
  make toolbox-ui
  ```

- **Run Toolbox on custom port (7000)**:

  ```bash
  make toolbox-port
  ```

Local Makefile targets load config from `agent/mcps/toolbox_alloydb.yaml`. Per-environment toolbox configs used by infrastructure live under `agent/mcps/<env>/` (for example `agent/mcps/dev/toolbox_alloydb.yaml`).

### 4. Vertex AI Agent Engine Deployment

Deploy the agent to Google Cloud Vertex AI Agent Runtime:

- **Dry-run validation** (validates configuration and OpenAPI schemas without cloud changes):

  ```bash
  export APP_ENV=dev
  make agent-deploy-dry
  ```

- **Deploy / update agent**:

  ```bash
  export APP_ENV=dev
  make agent-deploy
  ```

Under the hood, `make agent-deploy` generates `agent/utils/.requirements.txt` using `uv export` and runs `agent.utils.deploy` with idempotent create/update logic.

After a successful deploy, `_write_deployment_metadata` in [`agent/utils/deploy.py`](agent/utils/deploy.py) writes `metadata/deployment_metadata.${APP_ENV}.json` with the deployed agent runtime ID, display name, service account, environment, and timestamp. Use that file to inspect the latest deployment for the active `APP_ENV`.

See [`metadata/deployment_metadata.example.json`](metadata/deployment_metadata.example.json) for the metadata schema (keys only; values are filled at deploy time).

---

## Repository Structure

```text
├── .env.example                 # Environment variables template
├── Makefile                     # Developer workflow and deployment commands
├── README.md                    # Root project documentation (this file)
├── images/                      # Architecture diagrams
├── pyproject.toml               # Python project configuration and dependencies
├── uv.lock                      # Locked dependency graph
├── metadata/                    # Auto-generated deployment info (per APP_ENV)
│   └── deployment_metadata.example.json  # Schema example (empty values)
├── manifests/                   # Static Vertex AI Agent Runtime manifests
│   ├── README.md                # Manifest schema & deployment guide
│   └── agent-manifest.example.yaml
├── agent/                       # Core agent application source code
│   ├── agent.py                 # ADK agent definition & toolset registration
│   ├── agent_runtime_app.py     # Vertex AI AdkApp runtime wrapper & telemetry
│   ├── prompt.py                # System instructions & knowledge base prompts
│   ├── guards/                  # Custom security guards
│   ├── plugins/                 # ADK plugins (e.g. ModelArmorPlugin)
│   ├── mcps/                    # MCP Toolbox YAML configs (root + per environment)
│   └── utils/                   # Telemetry, typing, config, and deploy scripts
└── deployment/                  # Infrastructure as Code (Terraform)
    ├── README.md                # Infrastructure & AlloyDB bootstrap guide
    ├── environments/            # Per-environment Terraform root configs (e.g. dev, staging)
    ├── modules/                 # Modular Terraform components (VPC, AlloyDB, Cloud Run, etc.)
    └── shared/                  # Shared SQL, schemas, and supporting artifacts
```

---

## Suggested End-to-End Flow

1. **Provision infrastructure** — follow [`deployment/README.md`](deployment/README.md) (Terraform + AlloyDB bootstrap).
2. **Configure the app** — create `.env.${APP_ENV}` and `manifests/agent-manifest.${APP_ENV}.yaml`.
3. **Develop locally** — `make run-agent` and optional local Toolbox targets.
4. **Deploy the agent** — `make agent-deploy-dry`, then `make agent-deploy`.

---

## Detailed Documentation

- [Infrastructure & AlloyDB Bootstrap Guide](deployment/README.md)
- [Vertex AI Manifest & Runtime Configuration](manifests/README.md)
