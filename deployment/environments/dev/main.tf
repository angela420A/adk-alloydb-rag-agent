module "network" {
  source     = "../../modules/network"
  project_id = var.project_id
  region     = var.region
  env        = var.env

  ip_cidr_range     = var.ip_cidr_range
  psa_address       = var.psa_address
  psa_prefix_length = var.psa_prefix_length

  depends_on = [google_project_service.enable]
}

module "model_armor" {
  source     = "../../modules/model_armor"
  project_id = var.project_id
  region     = var.region
  env        = var.env

  depends_on = [google_project_service.enable]
}

module "psc" {
  source     = "../../modules/psc"
  project_id = var.project_id
  region     = var.region
  env        = var.env

  network_id = module.network.network_id
  subnet_id  = module.network.subnet_id

  psc_googleapis_ip = var.psc_googleapis_ip

  depends_on = [google_project_service.enable, module.network]
}

module "dns" {
  source     = "../../modules/dns"
  project_id = var.project_id
  region     = var.region
  env        = var.env

  network_id         = module.network.network_id
  psc_googleapis_ip  = module.psc.psc_googleapis_ip
  psc_model_armor_ip = module.psc.psc_model_armor_ip

  depends_on = [google_project_service.enable, module.network, module.psc]
}

# Including optinoal config
module "alloydb" {
  source     = "../../modules/alloydb"
  project_id = var.project_id
  region     = var.region
  env        = var.env

  network_id  = module.network.network_id
  psa_ip_name = module.network.psa_ip_name

  alloydb_password = var.alloydb_password

  depends_on = [google_project_service.enable, module.network]
}

# iam + secret manager
module "iam" {
  source     = "../../modules/iam"
  project_id = var.project_id
  region     = var.region
  env        = var.env

  alloydb_password = var.alloydb_password
  tools_yaml_path  = var.tools_yaml_path

  depends_on = [google_project_service.enable]
}

module "cloud_run" {
  source     = "../../modules/cloud_run"
  project_id = var.project_id
  region     = var.region
  env        = var.env

  network_id = module.network.network_id
  subnet_id  = module.network.subnet_id

  service_account_email      = module.iam.toolbox_identity_email
  invoker_service_account    = [module.iam.agent_runtime_email]
  alloydb_password_secret_id = module.iam.alloydb_password_secret_id
  tools_yaml_secret_id       = module.iam.tools_yaml_secret_id

  alloydb_host     = module.alloydb.primary_instance_ip
  alloydb_cluster  = module.alloydb.cluster_short_id
  alloydb_instance = module.alloydb.primary_instance_short_id
  alloydb_database = var.alloydb_database

  depends_on = [google_project_service.enable, module.iam, module.alloydb]
}

module "compute" {
  source     = "../../modules/compute"
  project_id = var.project_id
  region     = var.region
  zone       = var.zone
  env        = var.env

  subnet_id             = module.network.subnet_id
  service_account_email = module.iam.bastion_email

  depends_on = [google_project_service.enable, module.network, module.iam]
}

module "gcs" {
  source     = "../../modules/gcs"
  project_id = var.project_id
  region     = var.region
  env        = var.env

  agent_runtime_email = module.iam.agent_runtime_email

  depends_on = [google_project_service.enable, module.iam]
}