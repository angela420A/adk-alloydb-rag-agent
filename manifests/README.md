# Vertex AI Agent Runtime Manifest Guide (`manifests/`)

This directory contains static configuration manifests for deploying the **GamaPlay Agent** to Google Cloud Vertex AI Agent Runtime (Reasoning Engine).

---

## 📁 Manifest Directory Structure

```text
manifests/
├── agent-manifest.example.yaml   # Template for creating new environment manifests
└── README.md                     # This documentation guide
```

---

## ⚙️ Manifest Schema & Field Reference

Each environment manifest (`agent-manifest.<APP_ENV>.yaml`, e.g., `agent-manifest.dev.yaml`) defines the static metadata, entrypoint, and compute specifications for the Agent Runtime container:

```yaml
# ==============================================================================
# Vertex AI Agent Runtime Manifest Configuration (Example)
# ==============================================================================

# Display name for the Vertex AI Agent Engine resource
name: "my-cool-agent-dev"

# Root directory of the agent source code
agent_directory: "gamaplay_agent"

# Target GCP region
region: "us-central1"

# Enable Agent2Agent (A2A) protocol (recorded in deployment metadata)
is_a2a: false

# Target Python runtime version
python_version: "3.13"

# Entrypoint module and instantiated object
entrypoint:
  module: "gamaplay_agent.agent_runtime_app"
  object: "agent_runtime"
  requirements_file: "gamaplay_agent/utils/.requirements.txt"

# Container resource limits & autoscaling
runtime_resources:
  cpu: "4"
  memory: "8Gi"
  container_concurrency: 9
  min_instances: 1
  max_instances: 10
```

### Field Descriptions

| Field | Type | Description | Example |
| :--- | :--- | :--- | :--- |
| `name` | `string` | Display name for the Vertex AI Reasoning Engine instance. | `"my-cool-agent-dev"` |
| `agent_directory` | `string` | Root folder containing the agent package to bundle and upload. | `"gamaplay_agent"` |
| `region` | `string` | GCP region for Vertex AI Agent Engine. | `"us-central1"` |
| `is_a2a` | `boolean` | Flag indicating whether the agent implements the A2A protocol. | `false` |
| `python_version` | `string` | Python version for the runtime container (`3.10`–`3.14`). | `"3.13"` |
| `entrypoint.module` | `string` | Python module containing the instantiated `AdkApp`. | `"gamaplay_agent.agent_runtime_app"` |
| `entrypoint.object` | `string` | Variable name of the `AdkApp` instance in the entrypoint module. | `"agent_runtime"` |
| `entrypoint.requirements_file` | `string` | Path to generated deployment dependencies. | `"gamaplay_agent/utils/.requirements.txt"` |
| `runtime_resources.cpu` | `string` | Number of vCPUs allocated per container instance. | `"4"` |
| `runtime_resources.memory` | `string` | Memory limit per container instance. | `"8Gi"` |
| `runtime_resources.container_concurrency` | `integer` | Maximum concurrent requests per container. | `9` |
| `runtime_resources.min_instances` | `integer` | Minimum instance count (set >= 1 to eliminate cold starts). | `1` |
| `runtime_resources.max_instances` | `integer` | Maximum autoscaling instance limit. | `10` |

---

## 🚀 Deployment Workflow

The Python deployment utility ([`gamaplay_agent/utils/deploy.py`](../gamaplay_agent/utils/deploy.py)) automatically reads the corresponding manifest based on `APP_ENV`:

```
                    ┌─────────────────────────┐
                    │      export APP_ENV     │
                    └────────────┬────────────┘
                                 │
                 ┌───────────────┴───────────────┐
                 ▼                               ▼
     ┌───────────────────────┐       ┌───────────────────────┐
     │  .env.${APP_ENV}      │       │ manifests/agent-      │
     │  (Dynamic Runtime     │       │ manifest.${APP_ENV}   │
     │   Secrets & Config)   │       │ (Static Specs)        │
     └───────────┬───────────┘       └───────────┬───────────┘
                 │                               │
                 └───────────────┬───────────────┘
                                 ▼
                     ┌───────────────────────┐
                     │   deploy.py Pipeline  │
                     │  1. uv export deps    │
                     │  2. Dynamic Introspect│
                     │  3. Idempotent Deploy │
                     │  4. Save Metadata     │
                     └───────────┬───────────┘
                                 ▼
                     ┌───────────────────────┐
                     │ Vertex AI Agent Engine│
                     └───────────────────────┘
```

### 1. Creating a New Environment Manifest
To configure a new environment (e.g. `dev`, `staging`, or `prod`):

```bash
cp manifests/agent-manifest.example.yaml manifests/agent-manifest.dev.yaml
```

Edit `manifests/agent-manifest.dev.yaml` to specify your project-specific `name`, `region`, and resource limits.

### 2. Validating the Manifest (Dry-Run)
Test schema generation, class method introspection, and configuration without deploying:

```bash
export APP_ENV=dev
make agent-deploy-dry
```

### 3. Deploying to Vertex AI
Deploy or update the Agent Engine on Google Cloud:

```bash
export APP_ENV=dev
make agent-deploy
```

Upon successful deployment, deployment metadata is recorded in `metadata/deployment_metadata.${APP_ENV}.json`.
