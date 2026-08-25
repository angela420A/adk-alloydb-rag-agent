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
  default = "dev"
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

variable "alloydb_database" {
  type        = string
  default     = "agent_kb"
  description = "Database the Toolbox connects to. Terraform does not create it; run CREATE DATABASE manually first"
}


# secret manager - toolbox tools.yaml
variable "tools_yaml_path" {
  type        = string
  description = "Path to the MCP Toolbox tools.yaml for this environment, relative to environments/dev/"
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