variable "project_id" {
  type = string
}

variable "region" {
  type = string
}

variable "env" {
  type = string
}


variable "default_ai_platform_sa_roles" {
  type = list(string)
  default = [
    "roles/dns.peer",            # For Agent to set the DNS Peering
    "roles/compute.networkAdmin" # For Agent (Google Tenant Project) can add own Project Network Attachment (add in Accepted List)
  ]
  description = "Project-level IAM roles for Google-managed AI Platform service account"
}

variable "toolbox_identity_roles" {
  type = list(string)
  default = [
    "roles/alloydb.client",
    # "roles/secretmanager.secretAccessor",
    "roles/serviceusage.serviceUsageConsumer",
    "roles/logging.logWriter",
    "roles/monitoring.metricWriter",
  ]
  description = "Project-level IAM roles for toolbox-identity"
}

variable "agent_runtime_roles" {
  type = list(string)
  default = [
    "roles/aiplatform.user",
    "roles/modelarmor.user",
    "roles/logging.logWriter",
    "roles/cloudtrace.agent",
    "roles/monitoring.metricWriter",
    # "roles/storage.admin",
    "roles/serviceusage.serviceUsageConsumer"
  ]
  description = "Project-level IAM roles for the agent runtime identity"
}

variable "bastion_roles" {
  type = list(string)
  default = [
    "roles/alloydb.client",                    # alloydb.instances.connect, psql connection
    "roles/alloydb.viewer",                    # alloydb.instances.get, describe to fetch IP
    "roles/serviceusage.serviceUsageConsumer", # Required by AlloyDB connector
    "roles/logging.logWriter",
    "roles/monitoring.metricWriter",
  ]
  description = "Minimal IAM roles for the Bastion VM, avoiding default compute SA"
}

# secret manager
variable "alloydb_password" {
  type        = string
  sensitive   = true
  description = "AlloyDB password written to Secret Manager via TF_VAR_... environment variable."
}

variable "tools_yaml_path" {
  type        = string
  description = "File path to MCP Toolbox tools.yaml, e.g., ../../../agent/mcps/dev/toolbox_alloydb.yaml"
}

