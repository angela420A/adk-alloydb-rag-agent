# Agentic Agent — Infrastructure & Deployment

Terraform configuration and database bootstrap procedures for the Agentic Agent platform on Google Cloud.

| Environment | GCP Project | Region | State Bucket |
| :--- | :--- | :--- | :--- |
| **dev** | `<DEV_PROJECT_ID>` | `<DEV_REGION>` | `<DEV_TF_STATE_BUCKET>` |
| **staging** | `<STAGING_PROJECT_ID>` | `<STAGING_REGION>` | `<STAGING_TF_STATE_BUCKET>` |
| **prod** | `<PROD_PROJECT_ID>` | `<PROD_REGION>` | `<PROD_TF_STATE_BUCKET>` |

---

## 📁 Directory Layout

```text
deployment/
├── environments/        # Root modules per environment
│   ├── dev/             # Development environment configuration
│   ├── staging/         # Staging environment configuration
│   └── prod/            # Production environment configuration
└── modules/             # Shared Terraform modules
    ├── agent_runtime/   # Vertex AI Agent Runtime IAM & configurations
    ├── alloydb/         # AlloyDB cluster + primary instance + AI flags
    ├── bigquery/        # Telemetry dataset & views for agent logging
    ├── cloud_run/       # MCP Toolbox Cloud Run service
    ├── compute/         # Bastion VM (IAP SSH tunnel -> AlloyDB)
    ├── dns/             # Private DNS zones for PSC & Cloud Run peering
    ├── iam/             # Service accounts & Secret Manager secrets
    ├── model_armor/     # Model Armor template & security guardrails
    ├── network/         # VPC, subnets, PSA, and Cloud NAT
    ├── psc/             # Private Service Connect (PSC) endpoints & attachments
    └── storage/         # GCS buckets for telemetry and runtime artifacts
```

---

## 0. Prerequisites

Complete these steps **before** running `terraform init`:

1. **Create the Terraform State Bucket**:
   The bucket name must match `backend.tf` in the target environment:

   ```bash
   gcloud storage buckets create gs://<YOUR_TF_STATE_BUCKET_NAME> \
     --project=<YOUR_PROJECT_ID> \
     --location=<YOUR_REGION> \
     --uniform-bucket-level-access

   gcloud storage buckets update gs://<YOUR_TF_STATE_BUCKET_NAME> --versioning
   ```

2. **Authenticate with Google Cloud**:

   ```bash
   gcloud auth login --update-adc
   ```

3. **Export the AlloyDB Password**:
   Pass the database password via environment variable (never commit passwords to `terraform.tfvars`):

   ```bash
   export TF_VAR_alloydb_password='<YOUR_SECURE_PASSWORD>'
   ```

---

## 1. First-Time Environment Provisioning

A new environment requires a **three-phase bootstrap** because the MCP Toolbox on Cloud Run requires the target database to exist before it can start, while the database itself can only be created after AlloyDB is running.

Navigate to the target environment directory:

```bash
cd deployment/environments/<ENV>
terraform init
```

### Phase 1 — Core Infrastructure
Provision the VPC, IAM, AlloyDB, Bastion VM, and Storage. Cloud Run is intentionally excluded at this phase.

```bash
terraform plan \
  -target=module.network \
  -target=module.iam \
  -target=module.alloydb \
  -target=module.compute \
  -target=module.storage \
  -out=phase1.tfplan
```

Review the plan output, then apply:

```bash
terraform apply 'phase1.tfplan'
rm phase1.tfplan
```

> [!NOTE]
> AlloyDB cluster creation typically takes 15–20 minutes. `-target` is used only once during initial bootstrapping to resolve resource dependency ordering.

### Phase 2 — Database Bootstrap
Proceed to [Section 2: Database Bootstrap](#2-database-bootstrap) to create the database, vector extensions, and full-text indexes.

### Phase 3 — Remaining Infrastructure
Once the database is initialized, apply the entire configuration to provision Cloud Run, DNS, PSC, Agent Runtime, and BigQuery:

```bash
terraform plan -out=<ENV>.tfplan
terraform apply '<ENV>.tfplan'
rm <ENV>.tfplan
```

---

## 2. Database Bootstrap

Required **once per environment**. The database and its vector extensions are managed inside AlloyDB via PostgreSQL SQL scripts.

### 2.1 Open an IAP Tunnel to AlloyDB
AlloyDB uses Private IP only; all administrative access routes through the bastion VM via Identity-Aware Proxy (IAP).

Keep this terminal open:

```bash
export PROJECT_ID=<YOUR_PROJECT_ID>
export REGION=<YOUR_REGION>
export ZONE=<YOUR_ZONE>
export ADBCLUSTER=agentic-agent-<ENV>-alloydb
export ADBINSTANCE=agentic-agent-<ENV>-pr
export BASTION=agentic-agent-data-<ENV>-vm

export INSTANCE_IP=$(gcloud alloydb instances describe $ADBINSTANCE \
  --cluster=$ADBCLUSTER \
  --region=$REGION \
  --project=$PROJECT_ID \
  --format="value(ipAddress)")

gcloud compute ssh $BASTION \
  --zone=$ZONE \
  --project=$PROJECT_ID \
  --tunnel-through-iap \
  -- -N -L 8888:${INSTANCE_IP}:5432
```

*(Alternatively, run `terraform output -raw ssh_tunnel_command` for a pre-filled command).*

### 2.2 Create the Database
In a second terminal:

```bash
export DB_NAME=<YOUR_DATABASE_NAME> # e.g. agent_kb
export PGPASSWORD='<YOUR_SECURE_PASSWORD>'

psql "host=127.0.0.1 port=8888 user=postgres dbname=postgres sslmode=require" \
  -c "CREATE DATABASE ${DB_NAME};"
```

### 2.3 Enable Vector & AI Extensions
Run the following SQL commands in order:

```bash
psql "host=127.0.0.1 port=8888 user=postgres dbname=${DB_NAME} sslmode=require" \
  -c "CREATE EXTENSION IF NOT EXISTS vector;"

psql "host=127.0.0.1 port=8888 user=postgres dbname=${DB_NAME} sslmode=require" \
  -c "CREATE EXTENSION IF NOT EXISTS google_ml_integration CASCADE;"

psql "host=127.0.0.1 port=8888 user=postgres dbname=${DB_NAME} sslmode=require" \
  -c "CREATE EXTENSION IF NOT EXISTS alloydb_scann CASCADE;"
```

| Extension | Purpose |
| :--- | :--- |
| `vector` | pgvector for AlloyDB. Stores embeddings and executes nearest-neighbor similarity searches. |
| `google_ml_integration` | Provides `embedding()` and AI functions that invoke Vertex AI models directly from SQL. |
| `alloydb_scann` | ScaNN vector index for fast approximate nearest neighbor retrieval. |

### 2.4 Create Full-Text Search Index (GIN)
For hybrid search (Vector + Full-Text Search), create a `tsvector` column and a GIN index on your knowledge base table:

```sql
ALTER TABLE rag_documents
ADD COLUMN content_tsv tsvector
GENERATED ALWAYS AS (to_tsvector('english', content)) STORED;

CREATE INDEX rag_documents_content_tsv_idx
ON rag_documents USING GIN (content_tsv);
```

### 2.5 Verification
Verify that database flags and Vertex AI integration function properly:

```sql
SELECT extversion FROM pg_extension WHERE extname = 'google_ml_integration';
SHOW alloydb_ai_nl.enabled;
SHOW google_ml_integration.enable_faster_embedding_generation;
SHOW google_ml_integration.enable_preview_ai_functions;
SHOW scann.enable_preview_features;

-- Test embedding generation via Vertex AI
SELECT embedding('text-multilingual-embedding-002', 'hello world');
```

---

## 3. Day-to-Day Operations

After initial bootstrap, standard Terraform workflows apply directly:

```bash
cd deployment/environments/<ENV>
export TF_VAR_alloydb_password='<YOUR_SECURE_PASSWORD>'

terraform plan -out=<ENV>.tfplan
terraform apply '<ENV>.tfplan'
rm <ENV>.tfplan
```

### Useful Outputs

```bash
terraform output alloydb_host
terraform output toolbox_service_uri
terraform output psc_network_attachment
terraform output -raw ssh_tunnel_command
```

---

## 4. Important Notes & Architectural Constraints

- **Model Armor Regional Filters**: `Malicious URI filter` and `Multi-language detection` are currently supported in select regions (e.g. `us-central1`). For regions where these are not supported, set `enable_malicious_uri_filter=false` and `enable_multi_language_detection=false`.
- **PSC Network Attachment**: `producer_accept_lists` on the network attachment is populated automatically by Vertex AI Agent Runtime during agent deployment. Terraform ignores lifecycle changes to this field.
- **PSA IP Ranges**: Ensure non-overlapping CIDR blocks are assigned across environments (e.g., `10.73.8.0/24`, `10.73.16.0/24`, `10.73.24.0/24`).
- **MCP Toolbox Configuration**: The source of truth for database tools is located in `agent/mcps/<env>/toolbox_alloydb.yaml`. Terraform synchronizes this configuration to Secret Manager.
- **Provider Version Locking**: Always commit `.terraform.lock.hcl` for all environments to ensure reproducible deployments across CI/CD and local environments.
