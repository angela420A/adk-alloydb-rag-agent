resource "google_compute_network" "this" {
  project                      = var.project_id
  name                         = "gamaplay-agent-${var.env}-vpc"
  description                  = "The VPC network for Gama Play ${var.env} Agent."
  auto_create_subnetworks      = false
  enable_ula_internal_ipv6     = false
  routing_mode                 = "REGIONAL"
  bgp_best_path_selection_mode = "LEGACY"
}

# subnet
resource "google_compute_subnetwork" "this" {
  project                  = var.project_id
  name                     = "gamaplay-agent-${var.env}-subnet"
  description              = "The subnet for Gama Play ${var.env} Agent."
  ip_cidr_range            = var.ip_cidr_range
  region                   = var.region
  stack_type               = "IPV4_ONLY"
  network                  = google_compute_network.this.id
  private_ip_google_access = true
}

# firewall
resource "google_compute_firewall" "allow-ssh-iap" {
  project     = var.project_id
  name        = "gamaplay-agent-${var.env}-allow-ssh-iap"
  description = "Allow SSH from Google Identity-Aware Proxy"
  network     = google_compute_network.this.name


  direction = "INGRESS"
  priority  = 1000

  allow {
    protocol = "tcp"
    ports    = ["22"]
  }

  source_ranges = ["35.235.240.0/20"]
}

# private service access
resource "google_compute_global_address" "psa-ip-address" {
  project       = var.project_id
  name          = "psa-range-${var.env}"
  purpose       = "VPC_PEERING"
  address       = var.psa_address
  prefix_length = var.psa_prefix_length
  address_type  = "INTERNAL"
  description   = "VPC private service access for ${var.env}"
  network       = google_compute_network.this.id
}

resource "google_service_networking_connection" "psa_vpc_connection" {
  network                 = google_compute_network.this.id
  service                 = "servicenetworking.googleapis.com"
  reserved_peering_ranges = [google_compute_global_address.psa-ip-address.name]

  depends_on = [google_compute_network.this]
}

# cloud nat & router
resource "google_compute_router" "router" {
  name    = "gamaplay-agent-${var.env}-router"
  project = var.project_id
  region  = var.region
  network = google_compute_network.this.id
}

resource "google_compute_router_nat" "nat" {
  name                               = "gamaplay-agent-${var.env}-nat"
  router                             = google_compute_router.router.name
  region                             = var.region
  project                            = var.project_id
  nat_ip_allocate_option             = "AUTO_ONLY"
  source_subnetwork_ip_ranges_to_nat = "ALL_SUBNETWORKS_ALL_IP_RANGES"

  log_config {
    enable = true
    filter = "ERRORS_ONLY"
  }
}