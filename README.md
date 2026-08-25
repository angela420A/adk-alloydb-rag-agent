# GamaPlay Agent

An AI Agent service for the GamaPlay platform, built with Google Agent Development Kit (ADK), Google GenAI / Vertex AI, and Model Armor security guardrails.

---

## 🚀 Getting Started

### Prerequisites

- **Python**: `>= 3.13`
- **Package Manager**: [`uv`](https://docs.astral.sh/uv/)
- **Google Cloud SDK**: [`gcloud`](https://cloud.google.com/sdk/docs/install) CLI configured with appropriate permissions

### Installation

Clone the repository and install dependencies using `uv`:

```bash
uv sync
```

---

## ⚙️ Environment Setup (Required First Step)

> [!IMPORTANT]
> **Always set `APP_ENV` before running any commands, agent utilities, or `Makefile` targets!**
> 
> ```bash
> export APP_ENV=dev          # Choose from: dev, staging, prod
> ```
> 
> The application uses **Fail-Fast validation**: if `APP_ENV` is not set, the application will immediately halt to prevent running in the wrong environment.

### Environment Variables Template (`.env.example`)

Create your `.env.<APP_ENV>` file (e.g., `.env.dev`, `.env.staging`, `.env.prod`) by copying from [`.env.example`](.env.example):

```bash
cp .env.example .env.dev
```

Fill in the necessary values in your `.env.<APP_ENV>` file based on [`.env.example`](.env.example).

---

## 🛠️ Makefile Commands

All commands in the [`Makefile`](Makefile) require `APP_ENV` to be set in your environment.

### 1. Setup & Verification

Verify that your `APP_ENV` and corresponding `.env.${APP_ENV}` configuration are valid:

```bash
export APP_ENV=dev
make verify-env
```

### 2. Agent Development (ADK)

Run the agent locally with the ADK web interface:

```bash
make run-agent
```
*(Executes: `uv run --env-file .env.${APP_ENV} adk web`)*

### 3. MCP Toolbox for Databases

Download and manage the MCP Toolbox binary locally:

- **Download Toolbox binary**:
  ```bash
  make toolbox-dw
  ```
  *(Downloads version `v1.9.0` for macOS ARM64; check [mcp-toolbox releases](https://github.com/googleapis/mcp-toolbox/releases) for Linux or Windows builds)*

- **Run Toolbox locally**:
  ```bash
  make toolbox
  ```

- **Run Toolbox with Web UI**:
  ```bash
  make toolbox-ui
  ```

- **Run Toolbox on custom port (7000)**:
  ```bash
  make toolbox-port
  ```

### 4. Deploy Agent to Vertex AI / Agent Runtime

Deploy the agent to Google Cloud Agent Runtime:

- **Step 1: Create GCS Staging Bucket** (if it does not already exist):
  ```bash
  make agent-bucket
  ```
  *(Creates `gs://${GOOGLE_CLOUD_PROJECT}-agent-engine` with uniform bucket-level access and soft-delete retention)*

- **Step 2: Deploy Agent**:
  ```bash
  make agent-deploy
  ```
  *(Exports dependencies and deploys the agent using `gamaplay_agent.utils.deploy`)*

---

## 🏗️ Infrastructure & Deployment

Terraform configuration and database bootstrap instructions for AlloyDB and Cloud Run can be found in [`development/README.md`](development/README.md).
