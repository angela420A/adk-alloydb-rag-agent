output "toolbox_service_name" {
  value = google_cloud_run_v2_service.toolbox.name
}

output "service_uri" {
  value       = google_cloud_run_v2_service.toolbox.uri
  description = "Internal URI will be resolved to PSC IP by the run.app. zone in modules/dns"
}

output "service_id" {
  value = google_cloud_run_v2_service.toolbox.id
}