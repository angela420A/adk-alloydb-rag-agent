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
  type = string
}

variable "subnet_id" {
  type = string
}


# Compute - Postgres (Optional)----
# dev: e2-micro / e2-small, staging: e2-small / n1-standard-1, prod: e2-medium / n1-standard-1
variable "machine_type" {
  type    = string
  default = "n1-standard-1"
}

variable "deletion_protection" {
  type        = bool
  default     = false
  description = "prod should be true"
}

variable "boot_image" {
  type    = string
  default = "debian-cloud/debian-12"
}

# dev: 10, stag: 10-20, prod: 20-50
variable "boot_disk_size" {
  type    = number
  default = 10
}

variable "boot_disk_type" {
  type    = string
  default = "pd-balanced"
}

variable "network_ip" {
  type        = string
  default     = null
  description = "Static internal IP. Leave as null for GCP to allocate automatically to avoid collisions with Cloud Run / network attachment"
}

variable "service_account_email" {
  type        = string
  description = "Dedicated bastion SA, sourced from bastion_email in modules/iam"
}

variable "service_account_scopes" {
  type        = list(string)
  default     = ["cloud-platform"]
  description = "Actual permissions are controlled by IAM roles; keeping the scope as cloud-platform is sufficient"
}

variable "enable_secure_boot" {
  type        = bool
  default     = false
  description = "Can be safely enabled on Debian 12, but custom kernel modules will fail to load"
}

variable "enable_oslogin" {
  type        = bool
  default     = false
  description = "If true, use IAM to manage SSH accounts, but users will additionally require roles/compute.osLogin"
}

variable "network_tags" {
  type    = list(string)
  default = []
}