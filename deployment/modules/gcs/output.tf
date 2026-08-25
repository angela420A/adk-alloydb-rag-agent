output "bucket_name" {
  description = "GCS bucket name for Agent Runtime artifacts"
  value       = google_storage_bucket.agent_artifacts.name
}

output "bucket_url" {
  description = "gs:// URL for the Agent Runtime artifact bucket"
  value       = "gs://${google_storage_bucket.agent_artifacts.name}"
}

output "bucket_self_link" {
  value = google_storage_bucket.agent_artifacts.self_link
}
