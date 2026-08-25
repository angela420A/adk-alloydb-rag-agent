locals {
  all_services = toset(concat(
    var.agent_platform_one_services,
    var.agent_platform_two_services,
    var.rest_services,
    var.alloydb_services
  ))
}

resource "google_project_service" "enable" {
  for_each = local.all_services

  project            = var.project_id
  service            = each.value
  disable_on_destroy = false
}
