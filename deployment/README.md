# Agentic Agent — Infrastructure & Deployment

Terraform configuration and database bootstrap procedures for the Agentic Agent platform on Google Cloud.

Replace the placeholders below with your own project values before applying any environment.

| Environment | GCP Project | Region | State Bucket |
| :--- | :--- | :--- | :--- |
| **dev** | `<DEV_PROJECT_ID>` | `<DEV_REGION>` | `<DEV_TF_STATE_BUCKET>` |
| **staging** | `<STAGING_PROJECT_ID>` | `<STAGING_REGION>` | `<STAGING_TF_STATE_BUCKET>` |
| **prod** | `<PROD_PROJECT_ID>` | `<PROD_REGION>` | `<PROD_TF_STATE_BUCKET>` |

> This repo currently ships Terraform roots under `environments/dev` and `environments/staging`. You can add `prod` (or additional environments) by copying an existing environment directory and updating project, backend, and variable values.

---

## Directory Layout

```text
deployment/
├── environments/        # Root modules per environment
│   ├── dev/             # Development environment configuration
│   ├── staging/         # Staging environment configuration
│   └── prod/            # Optional: add when you are ready for production
├── modules/             # Shared Terraform modules
│   ├── agent_runtime/   # Vertex AI Agent Runtime IAM & configurations
│   ├── alloydb/         # AlloyDB cluster + primary instance + AI flags
│   ├── bigquery/        # Telemetry dataset & views for agent logging
│   ├── cloud_run/       # MCP Toolbox Cloud Run service
│   ├── compute/         # Bastion VM (IAP SSH tunnel -> AlloyDB)
│   ├── dns/             # Private DNS zones for PSC & Cloud Run peering
│   ├── iam/             # Service accounts & Secret Manager secrets
│   ├── model_armor/     # Model Armor template & security guardrails
│   ├── network/         # VPC, subnets, PSA, and Cloud NAT
│   ├── psc/             # Private Service Connect (PSC) endpoints & attachments
│   └── storage/         # GCS buckets for telemetry and runtime artifacts
└── shared/              # Shared SQL, schemas, and supporting artifacts
    ├── completions.sql
    ├── dummy_source.b64
    └── genai_logs_schema.json
```

---

## 0. Prerequisites

Complete these steps **before** running `terraform init`:

1. **Create the Terraform state bucket**  
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

3. **Export the AlloyDB password**  
   Pass the database password via environment variable (never commit passwords to `terraform.tfvars`):

   ```bash
   export TF_VAR_alloydb_password='<YOUR_SECURE_PASSWORD>'
   ```

---

## 1. First-Time Environment Provisioning

A new environment requires a **three-phase bootstrap** because:

- the MCP Toolbox on Cloud Run expects the target database to already exist before it can start cleanly, and
- the database can only be created after AlloyDB itself is running.

Navigate to the target environment directory:

```bash
cd deployment/environments/<ENV>
terraform init
```

### Phase 1 — Core Infrastructure

Provision the VPC, IAM, AlloyDB, bastion VM, and storage. Cloud Run is intentionally excluded in this phase.

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

Once the database is initialized, apply the full configuration to provision Cloud Run, DNS, PSC, Agent Runtime, and BigQuery:

```bash
terraform plan -out=<ENV>.tfplan
terraform apply '<ENV>.tfplan'
rm <ENV>.tfplan
```

---

## 2. Database Bootstrap

Required **once per environment**. The database and its vector extensions are managed inside AlloyDB via PostgreSQL SQL.

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

Alternatively, run `terraform output -raw ssh_tunnel_command` for a pre-filled command.

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

For hybrid search (vector + full-text search), create a `tsvector` column and a GIN index on your knowledge base table:

```sql
ALTER TABLE rag_documents
ADD COLUMN content_tsv tsvector
GENERATED ALWAYS AS (to_tsvector('english', content)) STORED;

CREATE INDEX rag_documents_content_tsv_idx
ON rag_documents USING GIN (content_tsv);
```

### 2.5 Verification

Verify that database flags and Vertex AI integration work as expected:

```sql
SELECT extversion FROM pg_extension WHERE extname = 'google_ml_integration';
SHOW alloydb_ai_nl.enabled;
SHOW google_ml_integration.enable_faster_embedding_generation;
SHOW google_ml_integration.enable_preview_ai_functions;
SHOW scann.enable_preview_features;

-- Test embedding generation via Vertex AI
SELECT embedding('text-multilingual-embedding-002', 'hello world');
```

### 2.6 Create Sample Hotels Table

Create the demo `hotels` table and load sample rows used by the MCP Toolbox hotel tools:

```bash
psql "host=127.0.0.1 port=8888 user=postgres dbname=${DB_NAME} sslmode=require" <<'SQL'
CREATE TABLE hotels(
  id            INTEGER NOT NULL PRIMARY KEY,
  name          VARCHAR NOT NULL,
  location      VARCHAR NOT NULL,
  price_tier    VARCHAR NOT NULL,
  checkin_date  DATE    NOT NULL,
  checkout_date DATE    NOT NULL,
  booked        BIT     NOT NULL
);

INSERT INTO hotels(id, name, location, price_tier, checkin_date, checkout_date, booked)
VALUES
  (1, 'Hilton Basel', 'Basel', 'Luxury', '2024-04-22', '2024-04-20', B'0'),
  (2, 'Marriott Zurich', 'Zurich', 'Upscale', '2024-04-14', '2024-04-21', B'0'),
  (3, 'Hyatt Regency Basel', 'Basel', 'Upper Upscale', '2024-04-02', '2024-04-20', B'0'),
  (4, 'Radisson Blu Lucerne', 'Lucerne', 'Midscale', '2024-04-24', '2024-04-05', B'0'),
  (5, 'Best Western Bern', 'Bern', 'Upper Midscale', '2024-04-23', '2024-04-01', B'0'),
  (6, 'InterContinental Geneva', 'Geneva', 'Luxury', '2024-04-23', '2024-04-28', B'0'),
  (7, 'Sheraton Zurich', 'Zurich', 'Upper Upscale', '2024-04-27', '2024-04-02', B'0'),
  (8, 'Holiday Inn Basel', 'Basel', 'Upper Midscale', '2024-04-24', '2024-04-09', B'0'),
  (9, 'Courtyard Zurich', 'Zurich', 'Upscale', '2024-04-03', '2024-04-13', B'0'),
  (10, 'Comfort Inn Bern', 'Bern', 'Midscale', '2024-04-04', '2024-04-16', B'0');
SQL
```

Confirm the rows loaded:

```bash
psql "host=127.0.0.1 port=8888 user=postgres dbname=${DB_NAME} sslmode=require" \
  -c "SELECT id, name, location, booked FROM hotels ORDER BY id;"
```

---

## 3. Day-to-Day Operations

After the initial bootstrap, use the standard Terraform workflow:

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

- **Model Armor regional filters**: The `Malicious URI filter` and `Multi-language detection` features are currently supported in select regions (for example `us-central1`). For regions where they are unavailable, set `enable_malicious_uri_filter=false` and `enable_multi_language_detection=false`.
- **PSC network attachment**: `producer_accept_lists` on the network attachment is populated automatically by Vertex AI Agent Runtime during agent deployment. Terraform ignores lifecycle changes to this field.
- **PSA IP ranges**: Assign non-overlapping CIDR blocks across environments (for example `10.73.8.0/24`, `10.73.16.0/24`, `10.73.24.0/24`).
- **MCP Toolbox configuration**: Per-environment database tool configs live under `agent/mcps/<env>/toolbox_alloydb.yaml` (for example `agent/mcps/dev/toolbox_alloydb.yaml`). Terraform synchronizes this configuration to Secret Manager. A root-level `agent/mcps/toolbox_alloydb.yaml` is also used by local Makefile Toolbox targets.
- **Provider version locking**: Always commit `.terraform.lock.hcl` for all environments so local and CI/CD runs stay reproducible.
