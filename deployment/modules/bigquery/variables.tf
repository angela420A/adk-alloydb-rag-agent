variable "project_name" {
  type = string
}

variable "project_id" {
  type = string
}

variable "region" {
  type = string
}

variable "env" {
  type = string
}

variable "logs_bucket_name" {
  type = string
}



# BigQuery Config (Optional) ----
variable "deletion_protection" {
  type        = bool
  default     = false
  description = "prod has to be true"
}