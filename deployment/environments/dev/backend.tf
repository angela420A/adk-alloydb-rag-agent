terraform {
  backend "gcs" {
    bucket = "qaaisys-tfstate"
    prefix = "gamaplay-agent/terraform/state"
  }
}