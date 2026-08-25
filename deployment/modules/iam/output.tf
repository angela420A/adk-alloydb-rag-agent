# cloud run - toolbox
output "toolbox_identity_email" {
  description = "Cloud Run service account for Toolbox"
  value       = google_service_account.toolbox_identity.email
}

output "agent_runtime_email" {
  description = "Agent Runtime service account for invoker role"
  value       = google_service_account.agent_runtime.email
}

# compute engine (postgres) - bastion
output "bastion_email" {
  value       = google_service_account.bastion.email
  description = "Used for service_account_email in modules/compute"
}


output "alloydb_password_secret_id" {
  value = google_secret_manager_secret.alloydb_password.secret_id
}

output "tools_yaml_secret_id" {
  description = "Secret used for mounting /app/tools.yaml in Cloud Run"
  value       = google_secret_manager_secret.tools_yaml.secret_id
}
