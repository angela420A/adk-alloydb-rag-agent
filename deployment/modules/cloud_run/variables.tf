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
  description = "AlloyDB cluster 短名稱，對應 tools.yaml 的 ALLOYDB_CLUSTER 佔位符"
}

variable "alloydb_instance" {
  type        = string
  description = "AlloyDB primary instance 短名稱，對應 tools.yaml 的 ALLOYDB_INSTANCE 佔位符"
}

variable "alloydb_database" {
  type        = string
  default     = "agent_kb"
  description = "Toolbox 連線的資料庫名稱。Terraform 不會建立這個 DB，需要事先手動 CREATE DATABASE"
}

variable "alloydb_user" {
  type    = string
  default = "postgres"
}

variable "tools_yaml_secret_id" {
  type        = string
  description = "來自 modules/iam 的 tools.yaml secret id"
}

variable "tools_mount_path" {
  type        = string
  default     = "/app"
  description = "tools.yaml 的掛載目錄。跟官方文件一致用 /app"
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