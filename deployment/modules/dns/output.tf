output "run_app_zone_id" {
  value = google_dns_managed_zone.run_app.id
}

output "run_app_zone_name" {
  value = google_dns_managed_zone.run_app.name
}

output "run_app_dns_name" {
  description = "Private DNS domain used to resolve Cloud Run via PSC (e.g. run.app.)"
  value       = google_dns_managed_zone.run_app.dns_name
}



output "model_armor_zone_id" {
  value = google_dns_managed_zone.model_armor.id
}

output "model_armor_zone_name" {
  value = google_dns_managed_zone.model_armor.name
}

output "model_armor_dns_name" {
  description = "Private DNS domain used to resolve Model Armor regional endpoints via PSC (e.g. rep.googleapis.com.)"
  value       = google_dns_managed_zone.model_armor.dns_name
}
