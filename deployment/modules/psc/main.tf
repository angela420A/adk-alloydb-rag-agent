# global
# Note: Global addresses with purpose = PRIVATE_SERVICE_CONNECT do not support automatic IP allocation.
# The address is required and must not fall within any subnet range.
resource "google_compute_global_address" "psc_googleapis" {
  project      = var.project_id
  name         = "psc-google-apis-${var.env}-ip"
  purpose      = "PRIVATE_SERVICE_CONNECT"
  address_type = "INTERNAL"
  address      = var.psc_googleapis_ip
  network      = var.network_id
}

resource "google_compute_global_forwarding_rule" "this" {
  name       = "pscgapis${var.env}"
  project    = var.project_id
  target     = "all-apis"
  network    = var.network_id
  ip_address = google_compute_global_address.psc_googleapis.id

  load_balancing_scheme = ""
}


# region
resource "google_compute_address" "psc_model_armor" {
  project      = var.project_id
  name         = "psc-model-armor-${var.env}-ip"
  region       = var.region
  purpose      = "GCE_ENDPOINT"
  address_type = "INTERNAL"
  subnetwork   = var.subnet_id
  description  = "Model Armor regional PSC endpoint IP (automatically allocated by subnet)"
}

resource "google_network_connectivity_regional_endpoint" "psc_model_armor" {
  project           = var.project_id
  name              = "psc-model-armor-${var.env}"
  location          = var.region
  target_google_api = "modelarmor.${var.region}.rep.googleapis.com"
  access_type       = "REGIONAL"
  address           = google_compute_address.psc_model_armor.id
  network           = var.network_id
  subnetwork        = var.subnet_id
  description       = "Model Armor regional endpoint for ${var.env}"
}


# network attachment
resource "google_compute_network_attachment" "agent_runtime" {
  project               = var.project_id
  name                  = "gamaplay-agent-${var.env}-attachment"
  region                = var.region
  description           = "Agent Runtime PSC interface into the ${var.env} VPC"
  connection_preference = "ACCEPT_MANUAL"
  subnetworks           = [var.subnet_id]

  # producer_accept_lists is populated by Agent Runtime during deployment.
  # Do not manage it here, otherwise the next apply will remove the tenant project added by Google.
  lifecycle {
    ignore_changes = [producer_accept_lists]
  }
}