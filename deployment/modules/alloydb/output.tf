output "cluster_id" {
  value = google_alloydb_cluster.agent_cluster.id
}

output "cluster_name" {
  value = google_alloydb_cluster.agent_cluster.name
}

output "cluster_short_id" {
  description = "Short name (without projects/... prefix), used for the cluster field in tools.yaml"
  value       = google_alloydb_cluster.agent_cluster.cluster_id
}

output "primary_instance_id" {
  value = google_alloydb_instance.primary.id
}

output "primary_instance_short_id" {
  description = "Short name, used for the instance field in tools.yaml"
  value       = google_alloydb_instance.primary.instance_id
}

output "primary_instance_ip" {
  value = google_alloydb_instance.primary.ip_address
}