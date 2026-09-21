resource "google_compute_instance" "bastion" {
  project      = var.project_id
  name         = "agentic-agent-data-${var.env}-vm"
  machine_type = var.machine_type
  zone         = var.zone
  description  = "Bastion host for psql access to AlloyDB over PSA peering"

  #   Allow automatic stopping when modifying fields such as machine type / service account to avoid destroying and recreating
  allow_stopping_for_update = true
  deletion_protection       = var.deletion_protection

  boot_disk {
    initialize_params {
      image = var.boot_image
      size  = var.boot_disk_size
      type  = var.boot_disk_type
    }
  }

  network_interface {
    subnetwork = var.subnet_id
    network_ip = var.network_ip
    stack_type = "IPV4_ONLY"

    # Omit access_config to avoid allocating an external IP; route traffic through Cloud NAT and SSH through IAP
  }

  service_account {
    email  = var.service_account_email
    scopes = var.service_account_scopes
  }

  shielded_instance_config {
    enable_secure_boot          = var.enable_secure_boot
    enable_vtpm                 = true
    enable_integrity_monitoring = true
  }

  metadata_startup_script = <<-EOT
    #!/bin/bash
    set -euo pipefail
    apt-get update
    apt-get install --yes postgresql-client
    timedatectl set-timezone Asia/Taipei
  EOT

  metadata = {
    enable-oslogin = var.enable_oslogin ? "TRUE" : "FALSE"
  }

  lifecycle {
    ignore_changes = [
      metadata["ssh-keys"]
    ]
  }

  tags = var.network_tags
}


# Set Compute engine who can access Postgres permission
# Project Level----
# Note: Users still require basic read permissions at the project level to query VM status via gcloud
resource "google_project_iam_member" "compute_viewer" {
  project = var.project_id
  role    = "roles/compute.viewer"
  # member  = "group:developers@yourcompany.com"
  member = "user:angelakuo@gamania.com"
}

# Resource Level----                                                                                                                                                                                                                                                                                                              
resource "google_iap_tunnel_instance_iam_member" "bastion_iap" {
  project  = var.project_id
  zone     = var.zone
  instance = google_compute_instance.bastion.name
  role     = "roles/iap.tunnelResourceAccessor"
  # member   = "group:developers@yourcompany.com"
  member = "user:angelakuo@gamania.com"
}

resource "google_compute_instance_iam_member" "bastion_oslogin" {
  project       = var.project_id
  zone          = var.zone
  instance_name = google_compute_instance.bastion.name
  role          = "roles/compute.osLogin"
  # member        = "group:developers@yourcompany.com"
  member = "user:angelakuo@gamania.com"
}