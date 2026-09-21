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
  name        = "toolbox-agentic-agent-${var.env}"
  location    = var.region
  description = "MCP Toolbox for Databases (Agentic Agent)"

  ingress = "INGRESS_TRAFFIC_INTERNAL_LOAD_BALANCER"

  deletion_protection = var.deletion_protection

  template {
    # iam: toolbox-identity
    service_account = var.service_account_email

    scaling {
      min_instance_count = var.min_instance_count
      max_instance_count = var.max_instance_count
    }

    vpc_access {
      network_interfaces {
        network    = var.network_id
        subnetwork = var.subnet_id
      }
      egress = "PRIVATE_RANGES_ONLY"
    }

    # Mount tools.yaml into the container as a secret volume,
    # equivalent to gcloud --set-secrets "/app/tools.yaml=<secret>:latest"
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

      # Toolbox does not look under /app by default; --tools-file must be set explicitly
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
        value = "UTC"
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

      # These map to ${...} placeholders in tools.yaml; Toolbox substitutes them at startup
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