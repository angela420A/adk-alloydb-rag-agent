# Service Account
# -------------------------
# Toolbox Cloud Run
resource "google_service_account" "toolbox_identity" {
  project      = var.project_id
  account_id   = "toolbox-identity-${var.env}"
  display_name = "Toolbox Cloud Run runtime identity (${var.env})"
  description  = "Cloud Run runtime identity used for connecting to AlloyDB and accessing Secret Manager"
}

resource "google_service_account" "agent_runtime" {
  project      = var.project_id
  account_id   = "gamaplay-agent-${var.env}"
  display_name = "Agent identity for Toolbox Cloud Run invoker (${var.env})"
  description  = "Caller identity granted roles/run.invoker"
}

# Compute Engine bastion (Alloydb postgres)
resource "google_service_account" "bastion" {
  project      = var.project_id
  account_id   = "gamaplay-bastion-${var.env}"
  display_name = "Bastion VM identity (${var.env})"
  description  = "VM identity for connecting via IAP and accessing AlloyDB using psql"
}


# Set member roles
# -------------------------
# cloud run - Toolbox
resource "google_project_iam_member" "toolbox_identity" {
  for_each = toset(var.toolbox_identity_roles)

  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.toolbox_identity.email}"
}

# agent runtime
resource "google_project_iam_member" "agent_runtime" {
  for_each = toset(var.agent_runtime_roles)

  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.agent_runtime.email}"
}

# compute engine - bastion
resource "google_project_iam_member" "bastion" {
  for_each = toset(var.bastion_roles)

  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.bastion.email}"
}



# Secret Manager
# -------------------------
# alloyDB password for Toolbox
resource "google_secret_manager_secret" "alloydb_password" {
  project   = var.project_id
  secret_id = "alloydb-password-${var.env}"

  replication {
    auto {}
  }

  labels = {
    env        = var.env
    managed_by = "terraform"
  }
}

resource "google_secret_manager_secret_version" "alloydb_password" {
  secret      = google_secret_manager_secret.alloydb_password.id
  secret_data = var.alloydb_password

  lifecycle {
    ignore_changes = [secret_data]
  }
}

resource "google_secret_manager_secret_iam_member" "toolbox_identity" {
  project   = var.project_id
  secret_id = google_secret_manager_secret.alloydb_password.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.toolbox_identity.email}"
}



# MCP Toolbox tools.yaml
# Toolbox 啟動時讀 /app/tools.yaml 來知道要暴露哪些 MCP tools。
# 這裡將 gamaplay_agent/mcps/<env>/toolbox_alloydb.yaml 的內容寫入 Secret Manager，
# 再由 Cloud Run 以 volume 的方式掛載進容器。
resource "google_secret_manager_secret" "tools_yaml" {
  project   = var.project_id
  secret_id = "toolbox-tools-${var.env}"

  replication {
    auto {}
  }

  labels = {
    env        = var.env
    managed_by = "terraform"
  }
}

# 使用 file() 而非 templatefile()：yaml 裡的 ${...} 是給 Toolbox 執行時替換用的，
# 用 templatefile() 會讓 Terraform 先去解析它並報錯。
resource "google_secret_manager_secret_version" "tools_yaml" {
  secret      = google_secret_manager_secret.tools_yaml.id
  secret_data = file(var.tools_yaml_path)

  # 不加 ignore_changes：tools.yaml 是設定檔，改了就要推新版本
}

resource "google_secret_manager_secret_iam_member" "tools_yaml_accessor" {
  project   = var.project_id
  secret_id = google_secret_manager_secret.tools_yaml.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.toolbox_identity.email}"
}
