# Cloud Run - Toolbox
resource "google_dns_managed_zone" "run_app" {
  project     = var.project_id
  name        = "run-app-internal-${var.env}"
  dns_name    = "run.app."
  description = "Private zone directing Cloud Run domain to PSC endpoint"
  visibility  = "private"

  private_visibility_config {
    networks {
      network_url = var.network_id
    }
  }
}

resource "google_dns_record_set" "run_app" {
  for_each = toset([
    "*.run.app.",
    "*.a.run.app.",
    "*.${var.region}.run.app.",
  ])

  project      = var.project_id
  managed_zone = google_dns_managed_zone.run_app.name
  name         = each.value
  type         = "A"
  ttl          = 300
  rrdatas      = [var.psc_googleapis_ip]
}


# Model Armor
resource "google_dns_managed_zone" "model_armor" {
  project     = var.project_id
  name        = "model-armor-${var.env}"
  dns_name    = "rep.googleapis.com."
  description = "Private zone directing regional endpoint to Model Armor PSC"
  visibility  = "private"

  private_visibility_config {
    networks {
      network_url = var.network_id
    }
  }
}

resource "google_dns_record_set" "model_armor" {
  project      = var.project_id
  managed_zone = google_dns_managed_zone.model_armor.name
  name         = "*.${google_dns_managed_zone.model_armor.dns_name}"
  type         = "A"
  ttl          = 300
  rrdatas      = [var.psc_model_armor_ip]
}