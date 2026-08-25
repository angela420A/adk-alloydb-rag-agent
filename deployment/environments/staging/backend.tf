terraform {
  backend "gcs" {
    bucket = "pl-agent-dev-tfstate"
    prefix = "gamaplay-agent/terraform/state"
  }
}