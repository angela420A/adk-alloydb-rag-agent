variable "project_id" {
  type = string
}

variable "region" {
  type = string
}

variable "env" {
  type = string
}


# (Optional)
variable "enable_malicious_uri_filter" {
  type        = bool
  default     = true
  description = "On GCP only support all US and EU region, not support Asia region"
}

variable "enable_multi_language_detection" {
  type        = bool
  default     = true
  description = "On GCP only support all US and EU region, not support Asia region"
}