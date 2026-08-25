output "psc_googleapis_id" {
  value = google_compute_global_address.psc_googleapis.id
}

output "psc_googleapis_ip" {
  value = google_compute_global_address.psc_googleapis.address
}

output "psc_googleapis_endpoint_id" {
  value = google_compute_global_forwarding_rule.this.id
}


output "psc_model_armor_id" {
  value = google_compute_address.psc_model_armor.id
}

output "psc_model_armor_ip" {
  value = google_compute_address.psc_model_armor.address
}

output "psc_model_armor_endpoint_id" {
  value = google_network_connectivity_regional_endpoint.psc_model_armor.id
}


output "agent_runtime_network_attachment_id" {
  value = google_compute_network_attachment.agent_runtime.id
}

output "agent_runtime_network_attachment_name" {
  description = "Network attachment short name used by Agent Runtime PSC interface"
  value       = google_compute_network_attachment.agent_runtime.name
}
