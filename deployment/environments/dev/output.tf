# Network
output "vpc_id" {
  description = "VPC network self link / id"
  value       = module.network.network_id
}

output "vpc_name" {
  description = "VPC network short name"
  value       = module.network.network_name
}


# PSC
output "psc_googleapis_ip" {
  value = module.psc.psc_googleapis_ip
}

output "psc_network_attachment" {
  description = "PSC network attachment name for Agent Runtime"
  value       = module.psc.agent_runtime_network_attachment_name
}

output "psc_network_attachment_id" {
  description = "PSC network attachment full resource id"
  value       = module.psc.agent_runtime_network_attachment_id
}


# AlloyDB
output "alloydb_host" {
  description = "Internal IP of AlloyDB for psql / SSH tunnel"
  value       = module.alloydb.primary_instance_ip
}

output "alloydb_database" {
  description = "AlloyDB database name used by Toolbox / Agent"
  value       = var.alloydb_database
}


# Model Armor
output "model_armor_template_id" {
  description = "Model Armor template ID"
  value       = module.model_armor.model_armor_template
}


# IAM
output "agent_service_account" {
  description = "Agent Runtime service account email (google_service_account.agent_runtime)"
  value       = module.iam.agent_runtime_email
}


# DNS
output "dns_run_app_domain" {
  description = "Private DNS domain for Cloud Run (run.app.)"
  value       = module.dns.run_app_dns_name
}

output "dns_model_armor_domain" {
  description = "Private DNS domain for Model Armor regional endpoints (rep.googleapis.com.)"
  value       = module.dns.model_armor_dns_name
}


# GCS
# output "agent_artifacts_bucket" {
#   description = "GCS bucket URL for Agent Runtime artifacts (gs://...)"
#   value       = module.gcs.bucket_url
# }

# output "agent_artifacts_bucket_name" {
#   description = "GCS bucket name for Agent Runtime artifacts"
#   value       = module.gcs.bucket_name
# }

# Storage
output "logs_bucket_name" {
  description = "GCS bucket name for Agent Runtime"
  value       = module.storage.logs_bucket_name
}


# Compute Engine
output "bastion_name" {
  description = "Target instance for gcloud compute ssh"
  value       = module.compute.instance_name
}


# Cloud Run - Toolbox
output "toolbox_service_uri" {
  value = module.cloud_run.service_uri
}


# Command to ssh tunnel to Postgres Compute Engine
output "ssh_tunnel_command" {
  description = "Command to establish AlloyDB tunnel, replacing the hardcoded IP version in Warp Drive"
  value       = "gcloud compute ssh ${module.compute.instance_name} --zone=${module.compute.zone} --tunnel-through-iap -- -N -L 8888:${module.alloydb.primary_instance_ip}:5432"
}
