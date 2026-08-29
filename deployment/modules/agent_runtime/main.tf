# Base64-encoded dummy source tarball for initial Agent Runtime creation.
locals {
  dummy_source_b64 = trimspace(file("${path.module}/../../shared/dummy_source.b64"))
}

resource "google_vertex_ai_reasoning_engine" "agent_runtime" {
  display_name = var.project_name
  description  = "Agent deployed via Terraform"
  region       = var.region
  project      = var.project_id

  spec {
    agent_framework = "google-adk"
    service_account = var.service_account_email

    deployment_spec {
      min_instances         = 1
      max_instances         = 10
      container_concurrency = 9

      resource_limits = {
        cpu    = "4"
        memory = "8Gi"
      }

      env {
        name  = "LOGS_BUCKET_NAME"
        value = var.logs_data_bucket_name
      }

      env {
        name  = "TZ"
        value = "Asia/Taipei"
      }

      env {
        name  = "OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT"
        value = "NO_CONTENT"
      }

      env {
        name  = "GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY"
        value = "true"
      }
    }

    source_code_spec {
      inline_source {
        source_archive = local.dummy_source_b64
      }

      python_spec {
        entrypoint_module  = "app.agent_runtime_app"
        entrypoint_object  = "agent_runtime"
        requirements_file  = "app/app_utils/.requirements.txt"
        version            = "3.12"
      }
    }
  }

  # Prevent subsequent Terraform runs from overwriting the deployed agent code back to the dummy source after deploy.py runs.
  lifecycle {
    ignore_changes = [
      spec[0].source_code_spec,
    ]
  }
}