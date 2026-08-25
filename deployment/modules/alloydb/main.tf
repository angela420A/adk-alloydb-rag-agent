resource "google_alloydb_cluster" "agent_cluster" {
  project    = var.project_id
  location   = var.region
  cluster_id = "gamaplay-agent-${var.env}-alloydb"

  database_version = var.database_version

  network_config {
    network            = var.network_id
    allocated_ip_range = var.psa_ip_name
  }

  initial_user {
    user     = var.alloydb_user
    password = var.alloydb_password
  }

  continuous_backup_config {
    enabled              = var.continuous_backup_config_enabled
    recovery_window_days = var.backup_recovery_window_days
  }

  # prod env true, else false
  deletion_protection = var.deletion_protection

  deletion_policy = var.deletion_policy
}

resource "google_alloydb_instance" "primary" {
  cluster       = google_alloydb_cluster.agent_cluster.name
  instance_id   = "gamaplay-agent-${var.env}-pr"
  instance_type = "PRIMARY"

  availability_type = var.availability_type

  machine_config {
    cpu_count = var.cpu_count

    # if null then N2
    machine_type = var.machine_type
  }

  database_flags = var.database_flags

  client_connection_config {
    ssl_config {
      ssl_mode = "ENCRYPTED_ONLY"
    }
  }

  query_insights_config {
    query_plans_per_minute  = 5
    query_string_length     = 1024
    record_application_tags = false
    record_client_address   = false
  }
}


# Set AlloyDB Google-managed service agent
resource "google_project_service_identity" "alloydb" {
  provider = google-beta

  project = var.project_id
  service = "alloydb.googleapis.com"
}

resource "google_project_iam_member" "alloydb_vertex_ai" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = google_project_service_identity.alloydb.member
}