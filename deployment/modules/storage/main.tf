# locals {
#   bucket_name = coalesce(var.bucket_name, "agentic-agent-${var.env}-artifacts")
# }

# resource "google_storage_bucket" "agent_artifacts" {
#   project                     = var.project_id
#   name                        = local.bucket_name
#   location                    = var.region
#   storage_class               = "STANDARD"
#   uniform_bucket_level_access = true
#   public_access_prevention    = "enforced"
#   force_destroy               = var.force_destroy

#   versioning {
#     enabled = true
#   }

#   labels = {
#     env        = var.env
#     managed_by = "terraform"
#     purpose    = "agent-runtime-artifacts"
#   }
# }

# # Set Agent SA storage roles
# resource "google_storage_bucket_iam_member" "agent_runtime_old" {
#   for_each = toset(var.agent_runtime_roles)

#   bucket = google_storage_bucket.agent_artifacts.name
#   role   = each.value
#   member = "serviceAccount:${var.agent_runtime_email}"
# }



resource "google_storage_bucket" "logs_data_bucket" {
  name     = "${var.project_id}-${var.project_name}-logs"
  project  = var.project_id
  location = var.region

  storage_class               = "STANDARD"
  uniform_bucket_level_access = true
  public_access_prevention    = "enforced"
  force_destroy               = var.force_destroy

  versioning {
    enabled = true
  }

  labels = {
    env        = var.env
    managed_by = "terraform"
    purpose    = "agent-runtime-artifacts"
  }
}

# Set bucket roles
resource "google_storage_bucket_iam_member" "agent_runtime" {
  for_each = toset(var.agent_runtime_roles)

  bucket = google_storage_bucket.logs_data_bucket.name
  role   = each.value
  member = "serviceAccount:${var.agent_runtime_email}"
}

resource "google_storage_bucket_iam_member" "vertex_ai_sa" {
  for_each = toset(var.agent_runtime_roles)

  bucket = google_storage_bucket.logs_data_bucket.name
  role   = each.value
  member = "serviceAccount:${var.vertex_ai_sa_email}"
}