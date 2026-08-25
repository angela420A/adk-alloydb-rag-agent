variable "project_id" {
  type = string
}

variable "region" {
  type = string
}

variable "env" {
  type = string
}

variable "ip_cidr_range" {
  type        = string
  description = "Primary subnet CIDR range. Cloud Run direct VPC egress and network attachments consume IPs from here (do not make it too small)"
}

variable "psa_address" {
  type        = string
  default     = null
  description = "Start IP address of the PSA range (e.g., 10.73.8.0). Set to null for GCP to automatically select. For multi-environment setups, specifying explicitly is recommended to prevent IP overlapping"
}

variable "psa_prefix_length" {
  type        = number
  description = "Prefix length of the PSA range. AlloyDB requires at least /24"
}
