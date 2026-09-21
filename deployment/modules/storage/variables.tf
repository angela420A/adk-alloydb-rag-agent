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

variable "agent_runtime_email" {
  type        = string
  description = "Agent Runtime service account email granted object access on the artifact bucket"
}

variable "vertex_ai_sa_email" {
  type        = string
  description = "The Google-managed Vertex AI (AI Platform) service account email"
}



variable "bucket_name" {
  type        = string
  default     = null
  description = "Optional explicit bucket name. Defaults to agentic-agent-<env>-artifacts"
}

variable "force_destroy" {
  type        = bool
  default     = false
  description = "Allow terraform destroy to delete non-empty bucket. Keep false outside throwaway envs"
}

variable "agent_runtime_roles" {
  type = list(string)
  default = [
    "roles/storage.objectAdmin",
    "roles/storage.legacyBucketReader",
  ]
  description = "Bucket-level IAM roles for the Agent Runtime service account"
}
