data "google_project" "this" {
  project_id = var.project_id
}

locals {
  # Google-managed service agent for Vertex AI Agent Engine
  agent_engine_service_agent = "serviceAccount:service-${data.google_project.this.number}@gcp-sa-aiplatform-re.iam.gserviceaccount.com"

  invoker_members = concat(
    [for sa in var.invoker_service_account : "serviceAccount:${sa}"],
    var.grant_agent_engine_invoker ? [local.agent_engine_service_agent] : []
  )
}

resource "google_cloud_run_v2_service" "toolbox" {
  project     = var.project_id
  name        = "toolbox-scm-agent-${var.env}"
  location    = var.region
  description = "The Toolbox for Service Center Management"

  ingress = "INGRESS_TRAFFIC_INTERNAL_LOAD_BALANCER"

  deletion_protection = var.deletion_protection

  template {
    # iam: toolbox-identity
    service_account = var.service_account_email

    scaling {
      max_instance_count = var.max_instance_count
    }

    vpc_access {
      network_interfaces {
        network    = var.network_id
        subnetwork = var.subnet_id
      }
      egress = "PRIVATE_RANGES_ONLY"
    }

    # 將 tools.yaml 以 secret volume 掛載進容器，
    # 等同於 gcloud 的 --set-secrets "/app/tools.yaml=<secret>:latest"
    volumes {
      name = "tools"
      secret {
        secret = var.tools_yaml_secret_id
        items {
          version = "latest"
          path    = "tools.yaml"
          mode    = 288 # 0440
        }
      }
    }

    containers {
      image = var.image

      # Toolbox 預設不會去 /app 找設定檔，必須明確指定 --tools-file
      args = [
        "--tools-file=${var.tools_mount_path}/tools.yaml",
        "--address=0.0.0.0",
        "--port=${var.container_port}",
      ]

      volume_mounts {
        name       = "tools"
        mount_path = var.tools_mount_path
      }

      ports {
        name           = "http1"
        container_port = var.container_port
      }

      env {
        name  = "GOOGLE_CLOUD_PROJECT"
        value = var.project_id
      }

      env {
        name  = "TZ"
        value = "Asia/Taipei"
      }

      env {
        name  = "GOOGLE_CLOUD_LOCATION"
        value = var.region
      }

      env {
        name = "ALLOYDB_PASSWORD"
        value_source {
          secret_key_ref {
            secret  = var.alloydb_password_secret_id
            version = "latest"
          }
        }
      }

      env {
        name  = "ALLOYDB_HOST"
        value = var.alloydb_host
      }

      # 以下對應 tools.yaml 裡的 ${...} 佔位符，Toolbox 啟動時會替換
      env {
        name  = "ALLOYDB_CLUSTER"
        value = var.alloydb_cluster
      }

      env {
        name  = "ALLOYDB_INSTANCE"
        value = var.alloydb_instance
      }

      env {
        name  = "ALLOYDB_DATABASE"
        value = var.alloydb_database
      }

      env {
        name  = "ALLOYDB_USER"
        value = var.alloydb_user
      }

      resources {
        startup_cpu_boost = true
      }
    }
  }
}


# Set Cloud Run Invoker permission
resource "google_cloud_run_v2_service_iam_member" "invokers" {
  for_each = toset(local.invoker_members)

  project  = var.project_id
  location = google_cloud_run_v2_service.toolbox.location
  name     = google_cloud_run_v2_service.toolbox.name
  role     = "roles/run.invoker"
  member   = each.value
}