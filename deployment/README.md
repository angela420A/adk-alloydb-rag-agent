# Gamaplay Agent — Infrastructure

Terraform configuration for the Gamaplay Agent platform.

| Environment | GCP Project | Region | State Bucket |
| --- | --- | --- | --- |
| dev | `qaaisys` | `us-central1` | `qaaisys-tfstate` |
| staging | `pl-agent-dev` | `asia-southeast1` | `pl-agent-dev-tfstate` |
| prod | TBD | TBD | TBD |

## Layout

```
development/
├── environments/        # One root module per environment
│   ├── dev/
│   └── staging/
└── modules/             # Shared modules
    ├── alloydb/         # AlloyDB cluster + primary instance + service agent IAM
    ├── cloud_run/       # MCP Toolbox service
    ├── compute/         # Bastion VM (IAP SSH -> AlloyDB)
    ├── dns/             # Private zones for PSC
    ├── gcs/             # Agent Runtime artifact bucket
    ├── iam/             # Service accounts + Secret Manager
    ├── model_armor/     # Model Armor template
    ├── network/         # VPC, subnet, NAT, PSA
    └── psc/             # PSC endpoints + network attachment
```

---

## 0. Prerequisites

Complete these **before** the first `terraform init`.

1. **Create the state bucket.** The name must match `backend.tf` in the target
   environment. Enable object versioning so state can be recovered.

   ```bash
   gcloud storage buckets create gs://<BUCKET_NAME> \
     --project=<PROJECT_ID> \
     --location=<REGION> \
     --uniform-bucket-level-access

   gcloud storage buckets update gs://<BUCKET_NAME> --versioning
   ```

2. **Authenticate.**

   ```bash
   gcloud auth login --update-adc
   ```

3. **Export the AlloyDB password.** Never put this in `terraform.tfvars`.

   ```bash
   export TF_VAR_alloydb_password='<password>'
   ```

---

## 1. First-time provisioning

A brand-new environment needs three phases, because the MCP Toolbox on Cloud Run
fails to start unless its target database already exists — and that database can
only be created after AlloyDB is running.

Run everything from the environment directory:

```bash
cd development/environments/<ENV>
terraform init
```

### Phase 1 — Core infrastructure

Provision the network, AlloyDB, IAM and the bastion VM. Cloud Run is
deliberately excluded at this point.

```bash
terraform plan \
  -target=module.network \
  -target=module.iam \
  -target=module.alloydb \
  -target=module.compute \
  -out=phase1.tfplan
```

Review the plan output, then apply exactly what you reviewed:

```bash
terraform apply 'phase1.tfplan'
rm phase1.tfplan
```

AlloyDB cluster creation takes roughly 15–20 minutes.

> `-target` is intended for exceptional situations, and Terraform will print a
> warning saying so. It is used here only to break the bootstrap
> chicken-and-egg problem, and only on the very first apply of an environment.

### Phase 2 — Database bootstrap

See [section 2](#2-database-bootstrap), then return here.

### Phase 3 — Everything else

```bash
terraform plan -out=<ENV>.tfplan
terraform apply '<ENV>.tfplan'
rm <ENV>.tfplan
```

Cloud Run now starts successfully because the database and its extensions exist.
The plan should show no `-target` warning and should converge on subsequent runs.

---

## 2. Database bootstrap

Required **once per environment**. The database and its extensions are not
managed by Terraform.

### 2.1 Open an IAP tunnel to AlloyDB

AlloyDB only has a private IP, so all access goes through the bastion VM.
Keep this terminal open for the rest of this section.

```bash
export PROJECT_ID=<PROJECT_ID>
export REGION=<REGION>
export ZONE=<ZONE>
export ADBCLUSTER=gamaplay-agent-<ENV>-alloydb
export ADBINSTANCE=gamaplay-agent-<ENV>-pr
export BASTION=gamaplay-agent-data-<ENV>-vm

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

`terraform output -raw ssh_tunnel_command` prints a ready-to-run version of the
command above once the bastion and AlloyDB exist.

### 2.2 Create the database

In a second terminal. `DB_NAME` must match the `alloydb_database` variable of
the environment (`agent_kb` for dev, `gamaplay_agent_kb_stag` for staging).

```bash
export DB_NAME=<DB_NAME>
export PGPASSWORD='<password>'

psql "host=127.0.0.1 port=8888 user=postgres dbname=postgres sslmode=require" \
  -c "CREATE DATABASE ${DB_NAME}"
```

### 2.3 Enable the extensions

Run these in order. Each one is created per database, not per instance.

```bash
psql "host=127.0.0.1 port=8888 user=postgres dbname=${DB_NAME} sslmode=require" \
  -c "CREATE EXTENSION IF NOT EXISTS vector;"

psql "host=127.0.0.1 port=8888 user=postgres dbname=${DB_NAME} sslmode=require" \
  -c "CREATE EXTENSION IF NOT EXISTS google_ml_integration CASCADE;"

psql "host=127.0.0.1 port=8888 user=postgres dbname=${DB_NAME} sslmode=require" \
  -c "CREATE EXTENSION IF NOT EXISTS alloydb_scann CASCADE;"
```

What each one provides:

| Extension | Purpose |
| --- | --- |
| `vector` | pgvector, customised for AlloyDB. Stores embeddings and runs nearest-neighbor search. |
| `google_ml_integration` | `embedding()` and other functions that call Vertex AI from SQL. |
| `alloydb_scann` | ScaNN vector index. `CASCADE` also installs `vector` if it is missing. |

`google_ml_integration` calls Vertex AI as the AlloyDB service agent. Terraform
already grants that agent `roles/aiplatform.user` in `modules/alloydb`, so no
manual `gcloud projects add-iam-policy-binding` step is needed.

#### Full-text search: RUM vs GIN

Hybrid search needs a full-text index alongside the ScaNN vector index. There
are two options.

**RUM** is faster for ranking and phrase search because it stores lexeme
positions in the posting tree. It is not always available:

- There is **no database flag** that enables it. If `rum.control` is missing,
  the extension simply is not built for that instance's PostgreSQL version.
  It is **not available on `POSTGRES_18`**, which is what these environments
  run, so expect to use GIN.
- It requires the `alloydbsuperuser` database role. The built-in `postgres`
  user has it; an IAM-based user does not unless granted explicitly.

Check availability first:

```sql
SELECT name, default_version FROM pg_available_extensions WHERE name = 'rum';
```

If it returns a row:

```bash
psql "host=127.0.0.1 port=8888 user=postgres dbname=${DB_NAME} sslmode=require" \
  -c "CREATE EXTENSION IF NOT EXISTS rum;"
```

**GIN** is the fallback and needs no extension at all — it is built into
PostgreSQL. Google's own `ai.hybrid_search()` example uses GIN:

```sql
ALTER TABLE rag_documents
ADD COLUMN content_tsv tsvector
GENERATED ALWAYS AS (to_tsvector('english', content)) STORED;

CREATE INDEX rag_documents_content_tsv_idx
ON rag_documents USING GIN (content_tsv);
```

GIN has to re-read the heap to compute relevance scores, so ranking is slower
than RUM. For hybrid search, where each side returns a small top-N before RRF
fusion, the difference is usually negligible.

### 2.4 Verify

Open a session against the new database:

```bash
psql "host=127.0.0.1 port=8888 user=postgres dbname=${DB_NAME} sslmode=require"
```

**Check the extension version:**

```sql
SELECT extversion FROM pg_extension WHERE extname = 'google_ml_integration';
```

**Check the database flags:**

```sql
SHOW alloydb_ai_nl.enabled;
SHOW google_ml_integration.enable_faster_embedding_generation;
SHOW google_ml_integration.enable_preview_ai_functions;
SHOW scann.enable_preview_features;
```

All four should report `on`. Terraform sets them through the `database_flags`
variable in `modules/alloydb`.

If any of them reports `off`, re-run `terraform apply` rather than using
`gcloud alloydb instances update`. The `--database-flags` argument **replaces the
entire flag set**, so applying it by hand would silently drop the other flags.
If you must do it manually, pass every flag at once:

```bash
gcloud beta alloydb instances update $ADBINSTANCE \
  --cluster=$ADBCLUSTER \
  --region=$REGION \
  --project=$PROJECT_ID \
  --database-flags \
alloydb_ai_nl.enabled=on,google_ml_integration.enable_faster_embedding_generation=on,google_ml_integration.enable_preview_ai_functions=on,scann.enable_preview_features=on \
  --update-mode=FORCE_APPLY
```

**Confirm embeddings work end to end:**

```sql
SELECT embedding('text-multilingual-embedding-002', 'hello world');
```

A permission error here means the AlloyDB service agent is missing
`roles/aiplatform.user`.

---

## 3. Day-to-day operations

Once an environment is bootstrapped, no tunnel is required for Terraform:

```bash
cd development/environments/<ENV>
export TF_VAR_alloydb_password='<password>'

terraform plan -out=<ENV>.tfplan
terraform apply '<ENV>.tfplan'
rm <ENV>.tfplan
```

> Plan files contain **all variable values in plaintext, including the AlloyDB
> password**. Delete them after use. `*.tfplan` is already in `.gitignore`.

### Useful outputs

```bash
terraform output alloydb_host
terraform output toolbox_service_uri
terraform output -raw ssh_tunnel_command
```

### Connecting to the database later

Reuse [section 2.1](#21-open-an-iap-tunnel-to-alloydb), then:

```bash
psql "host=127.0.0.1 port=8888 user=postgres dbname=<DB_NAME> sslmode=require"
```

---

## 4. Notes and known constraints

- **Model Armor regional support.** `Malicious URI filter` and
  `Multi-language detection` are unavailable in Asia regions. Staging sets
  `enable_malicious_uri_filter` and `enable_multi_language_detection` to
  `false`; dev in `us-central1` leaves them enabled.
- **`producer_accept_lists`** on the network attachment is written by Agent
  Runtime at deploy time. Terraform ignores changes to it on purpose.
- **PSA ranges must not overlap** across environments that might ever be peered:
  dev `10.73.8.0/24`, staging `10.73.16.0/24`, prod `10.73.24.0/24`.
- **Changing `psa_address` recreates the PSA range and therefore AlloyDB**,
  destroying all data.
- **`database_version` upgrades are in-place and forward-only.** Raising the
  value makes Terraform call the AlloyDB upgrade API on the existing cluster.
  Lowering it fails with `Target database version must be greater than the
  current database version`; the only way back is to destroy and recreate the
  cluster, losing all data and requiring a fresh bootstrap. Environments
  currently run `POSTGRES_18`.
- **Extension availability depends on the major version.** `rum` is not built
  for `POSTGRES_18`, so hybrid search uses a GIN index instead. Always check
  `pg_available_extensions` before assuming an extension exists.
- **Some database flags restart the instance.** `alloydb_ai_nl.enabled` and
  `scann.enable_preview_features` trigger a restart when added, removed or
  changed. `google_ml_integration.enable_faster_embedding_generation` and
  `google_ml_integration.enable_preview_ai_functions` do not.
- **Never set database flags with `gcloud`.** `--database-flags` replaces the
  entire set, so it silently drops any flag you omit. Terraform's
  `database_flags` variable is the single source of truth.
- **`psc_googleapis_ip` must not fall inside any subnet range.** A global
  `PRIVATE_SERVICE_CONNECT` address cannot be auto-allocated; it is always
  explicit.
- **`tools.yaml` lives in Secret Manager.** The source of truth is
  `gamaplay_agent/mcps/<env>/toolbox_alloydb.yaml`; Terraform pushes a new secret
  version whenever the file changes. All `${...}` placeholders are substituted by
  the Toolbox at runtime from Cloud Run environment variables.
- **`.terraform.lock.hcl` must be committed** for every environment so that all
  machines and CI resolve the same provider versions.
