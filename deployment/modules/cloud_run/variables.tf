variable "project_id" {
  type = string
}

variable "region" {
  type = string
}

variable "env" {
  type = string
}

variable "network_id" {
  type = string
}

variable "subnet_id" {
  type = string
}

variable "service_account_email" {
  type = string
}

variable "invoker_service_account" {
  type        = list(string)
  description = "SA email to be granted roles/run.invoker (excluding the serviceAccount: prefix)"
}

variable "alloydb_password_secret_id" {
  type = string
}

variable "alloydb_host" {
  type = string
}

variable "alloydb_cluster" {
  type        = string
  description = "AlloyDB cluster short name; maps to the ALLOYDB_CLUSTER placeholder in tools.yaml"
}

variable "alloydb_instance" {
  type        = string
  description = "AlloyDB primary instance short name; maps to the ALLOYDB_INSTANCE placeholder in tools.yaml"
}

variable "alloydb_database" {
  type        = string
  default     = "agent_kb"
  description = "Database name Toolbox connects to. Terraform does not create it; run CREATE DATABASE manually first"
}

variable "alloydb_user" {
  type    = string
  default = "postgres"
}

variable "tools_yaml_secret_id" {
  type        = string
  description = "tools.yaml secret id from modules/iam"
}

variable "tools_mount_path" {
  type        = string
  default     = "/app"
  description = "Mount directory for tools.yaml. Use /app to match the official docs"
}



# Cloud run config (Optional)---- 
variable "grant_agent_engine_invoker" {
  type        = bool
  default     = false
  description = "Whether to authorize the Vertex AI Agent Engine service agent to call this service"
}

variable "deletion_protection" {
  type        = bool
  default     = false
  description = "dev: false, prod: true"
}

variable "min_instance_count" {
  type        = number
  default     = 0
  description = "prod env can more"
}

variable "max_instance_count" {
  type        = number
  default     = 20
  description = "prod env can more"
}

variable "image" {
  type        = string
  default     = "us-central1-docker.pkg.dev/database-toolbox/toolbox/toolbox:latest"
  description = "MCP Toolbox image. The registry host is fixed to us-central1 and should not change with var.region"
}

variable "container_port" {
  type    = number
  default = 8080
}