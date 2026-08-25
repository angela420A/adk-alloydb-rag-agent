variable "project_id" {
  type = string
}

variable "region" {
  type = string
}

variable "zone" {
  type = string
}

variable "env" {
  type    = string
  default = "staging"
}


# network----
variable "ip_cidr_range" {
  type        = string
  description = "Primary subnet CIDR range. Cloud Run direct VPC egress and network attachments consume IPs from here (do not make it too small)"
}

variable "psa_address" {
  type        = string
  default     = null
  description = "Start IP address of the PSA range. Changing this will trigger recreation of the PSA range and subsequently AlloyDB"
}

variable "psa_prefix_length" {
  type        = number
  description = "Prefix length of the PSA range. AlloyDB requires at least /24"
}


# model armor----
# (Optional)
variable "enable_malicious_uri_filter" {
  type        = bool
  default     = false
  description = "On GCP only support all US and EU region, not support Asia region"
}

variable "enable_multi_language_detection" {
  type        = bool
  default     = false
  description = "On GCP only support all US and EU region, not support Asia region"
}


# psc----
variable "psc_googleapis_ip" {
  type        = string
  description = "Global PSC endpoint IP. Must not fall inside ip_cidr_range or any other subnet range"
}


# alloydb----
variable "alloydb_password" {
  type      = string
  sensitive = true
}

# (Optional)
variable "alloydb_database" {
  type        = string
  default     = "gamaplay_agent_kb_stag"
  description = "Database the Toolbox connects to. Terraform does not create it; run CREATE DATABASE manually first"
}

variable "continuous_backup_config_enabled" {
  type        = bool
  default     = true
  description = "dev can be false, other env has to be true"
}

variable "deletion_policy" {
  type        = string
  default     = "DEFAULT"
  description = "dev: 'FORCE', prd: null or 'DEFAULT'"
}

variable "availability_type" {
  type        = string
  default     = "REGIONAL"
  description = "REGIONAL for HA; use ZONAL in dev to save cost"
}


# secret manager----
# toolbox tools.yaml
variable "tools_yaml_path" {
  type        = string
  description = "Path to the MCP Toolbox tools.yaml for this environment, relative to environments/dev/"
}


# Compute Engine - Postgres
# (Optional)
variable "enable_secure_boot" {
  type        = bool
  default     = true
  description = "Can be safely enabled on Debian 12, but custom kernel modules will fail to load"
}

variable "enable_oslogin" {
  type        = bool
  default     = true
  description = "If true, use IAM to manage SSH accounts, but users will additionally require roles/compute.osLogin"
}


variable "agent_platform_one_services" {
  type = list(string)
  default = [
    "agentregistry.googleapis.com",
    "aiplatform.googleapis.com",
    "apphub.googleapis.com",
    "apptopology.googleapis.com",
    "cloudapiregistry.googleapis.com",
    "cloudtrace.googleapis.com",
    "compute.googleapis.com",
    "dataform.googleapis.com",
    "iam.googleapis.com",
    "iamconnectors.googleapis.com",
    "iap.googleapis.com",
    "logging.googleapis.com",
    "modelarmor.googleapis.com",
    "monitoring.googleapis.com",
    "notebooks.googleapis.com",
    "observability.googleapis.com"
  ]
}

variable "agent_platform_two_services" {
  type = list(string)
  default = [
    "securitycenter.googleapis.com",
    "saasservicemgmt.googleapis.com",
    "storage.googleapis.com",
    "telemetry.googleapis.com",
    "texttospeech.googleapis.com",
    "networkconnectivity.googleapis.com",
    "networksecurity.googleapis.com",
    "networkservices.googleapis.com",
    "servicedirectory.googleapis.com"
  ]
}

variable "rest_services" {
  type = list(string)
  default = [
    "run.googleapis.com",
    "artifactregistry.googleapis.com",
    "cloudbuild.googleapis.com",
    "dns.googleapis.com",
    "secretmanager.googleapis.com"
  ]
}

variable "alloydb_services" {
  type = list(string)
  default = [
    "alloydb.googleapis.com",
    "compute.googleapis.com",
    "cloudresourcemanager.googleapis.com",
    "servicenetworking.googleapis.com",
    "aiplatform.googleapis.com"
  ]
}