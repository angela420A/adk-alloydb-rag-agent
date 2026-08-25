output "network_id" {
  value = google_compute_network.this.id
}

output "network_name" {
  description = "VPC network short name"
  value       = google_compute_network.this.name
}

output "subnet_id" {
  value = google_compute_subnetwork.this.id
}

output "subnet_ip" {
  value = google_compute_subnetwork.this.gateway_address
}

output "firewall_id" {
  value = google_compute_firewall.allow-ssh-iap.id
}

output "psa_ip_id" {
  value = google_compute_global_address.psa-ip-address.id
}

output "psa_ip_name" {
  value = google_compute_global_address.psa-ip-address.name
}

output "psa_ip" {
  value = google_compute_global_address.psa-ip-address.address
}

output "psa_vpc_connection_id" {
  value = google_service_networking_connection.psa_vpc_connection.id
}

output "cloud_router_id" {
  value = google_compute_router.router.id
}

output "cloud_nat_id" {
  value = google_compute_router_nat.nat.id
}


