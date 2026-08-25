output "instance_id" {
  value = google_compute_instance.bastion.id
}

output "instance_name" {
  value       = google_compute_instance.bastion.name
  description = "Instance name to use for gcloud compute ssh"
}

output "internal_ip" {
  value = google_compute_instance.bastion.network_interface[0].network_ip
}

output "zone" {
  value = google_compute_instance.bastion.zone
}