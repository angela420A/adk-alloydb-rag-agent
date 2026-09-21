terraform {
  backend "gcs" {
    # Replace {GOOGLE_CLOUD_PROJECT} with your GCP Project ID.
    # Example: if project ID is my-gcp-project, bucket becomes "my-gcp-project-tfstate".
    bucket = "{GOOGLE_CLOUD_PROJECT}-tfstate"
    prefix = "agentic-agent/terraform/state"
  }
}
