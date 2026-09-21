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

variable "psa_ip_name" {
  type        = string
  description = "The PSA name from VPC"
}

variable "alloydb_password" {
  type      = string
  sensitive = true
}



# AlloyDB Config (Optional) ----
variable "database_version" {
  type        = string
  default     = "POSTGRES_18"
  description = <<-EOT
    PostgreSQL major version.
    Raising this value performs an in-place major version UPGRADE through the
    AlloyDB upgrade API. Upgrades are forward-only: lowering the value fails with
    "Target database version must be greater than the current database version".
    To move to an older major version you must destroy and recreate the cluster,
    which loses all data.
    Note: not every extension is built for every major version. `rum` is not
    available on POSTGRES_18 - see the RUM vs GIN section in development/README.md.
  EOT
}

variable "alloydb_user" {
  type    = string
  default = "postgres"
}

variable "continuous_backup_config_enabled" {
  type        = bool
  default     = false
  description = "dev can be false, other env has to be true"
}

variable "backup_recovery_window_days" {
  type    = number
  default = 14
}

variable "deletion_protection" {
  type        = bool
  default     = false
  description = "prod has to be true"
}

variable "deletion_policy" {
  type        = string
  default     = "FORCE"
  description = "dev: 'FORCE', prd: null or 'DEFAULT'"
}

variable "availability_type" {
  type        = string
  default     = "ZONAL"
  description = "REGIONAL for HA; use ZONAL in dev to save cost"
}

variable "cpu_count" {
  type        = number
  default     = 2
  description = "prod can add more count"
}

variable "machine_type" {
  type        = string
  default     = null
  description = "The `cpu_count` match the number of vCPUs in the machine type. If null then N2"
}

variable "database_flags" {
  type        = map(string)
  description = <<-EOT
    Instance-level database flags. Terraform is the single source of truth here:
    `gcloud alloydb instances update --database-flags` REPLACES the entire set,
    so never set these by hand or the other flags get silently dropped.
  EOT
  default = {
    # AlloyDB AI natural language features. Restarts the instance.
    "alloydb_ai_nl.enabled" = "on"

    # Faster Vertex AI embedding generation. No restart.
    "google_ml_integration.enable_faster_embedding_generation" = "on"

    # Preview AI functions such as ai.hybrid_search(). No restart.
    "google_ml_integration.enable_preview_ai_functions" = "on"

    # ScaNN preview features: auto index maintenance, deferred index creation,
    # four-level tree indexes. Restarts the instance.
    "scann.enable_preview_features" = "on"

    # Session display timezone for TIMESTAMPTZ output (does NOT change stored UTC data)
    "timezone" = "UTC"
  }
}
