# Secret Manager Module

variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "secrets_to_create" {
  description = "Map of secrets to create"
  type        = map(string)
}

variable "project_labels" {
  description = "Labels for resources"
  type        = map(string)
  default     = {}
}

variable "gke_workload_sa_email" {
  description = "GKE workload service account email"
  type        = string
}

# Create secrets (placeholders only, values added manually)
resource "google_secret_manager_secret" "api_keys" {
  for_each = var.secrets_to_create

  project   = var.project_id
  secret_id = each.key
  labels    = var.project_labels

  replication {
    auto {}
  }
}

# Grant GKE workload SA access to secrets
resource "google_secret_manager_secret_iam_member" "gke_workload_access" {
  for_each = var.secrets_to_create  

  project   = var.project_id
  secret_id = each.key  # Use key directly
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${var.gke_workload_sa_email}"

  depends_on = [google_secret_manager_secret.api_keys]
}

# Outputs
output "secrets_created" {
  value = {
    for name, secret in google_secret_manager_secret.api_keys :
    name => {
      id   = secret.id
      name = secret.name
    }
  }
  description = "Created secrets (values must be added manually)"
}
