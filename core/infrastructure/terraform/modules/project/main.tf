# GCP Project Module
# Sets up required APIs and service accounts

variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "project_labels" {
  description = "Labels for resources"
  type        = map(string)
  default     = {}
}

# Enable required APIs
resource "google_project_service" "required_apis" {
  for_each = toset([
    "container.googleapis.com",           # GKE
    "compute.googleapis.com",             # Compute Engine
    "aiplatform.googleapis.com",          # Vertex AI
    "storage-api.googleapis.com",         # Cloud Storage
    "secretmanager.googleapis.com",       # Secret Manager
    "artifactregistry.googleapis.com",    # Artifact Registry
    "cloudresourcemanager.googleapis.com", # Resource Manager
    "iam.googleapis.com",                 # IAM
    "servicenetworking.googleapis.com",   # Service Networking
    # "cloudrun.googleapis.com",            # Cloud Run
    "monitoring.googleapis.com",          # Cloud Monitoring
    "logging.googleapis.com",             # Cloud Logging
  ])

  project            = var.project_id
  service            = each.value
  disable_on_destroy = false
}

# Platform Development Service Account
resource "google_service_account" "platform_dev" {
  project      = var.project_id
  account_id   = "platform-dev-sa"
  display_name = "Platform Development Service Account"
  description  = "Service account for platform development and deployment"
}

# IAM Roles for Platform Service Account
resource "google_project_iam_member" "platform_dev_roles" {
  for_each = toset([
    "roles/container.admin",           # GKE management
    "roles/storage.admin",             # Storage access
    "roles/aiplatform.user",           # Vertex AI access
    "roles/secretmanager.admin",       # Secrets management
    "roles/artifactregistry.writer",   # Push images
    "roles/run.admin",                 # Cloud Run deployment
    "roles/iam.serviceAccountUser",    # Act as service accounts
    "roles/monitoring.metricWriter",   # Write metrics
    "roles/logging.logWriter",         # Write logs
  ])

  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.platform_dev.email}"
}

# Service Account for GKE Workloads (Workload Identity)
resource "google_service_account" "gke_workload" {
  project      = var.project_id
  account_id   = "platform-gke-workload"
  display_name = "Platform GKE Workload Identity"
  description  = "Service account for platform services running in GKE"
}

# IAM Roles for GKE Workload Service Account
resource "google_project_iam_member" "gke_workload_roles" {
  for_each = toset([
    "roles/storage.objectViewer",         # Read from GCS
    "roles/aiplatform.user",              # Use Vertex AI
    "roles/secretmanager.secretAccessor", # Read secrets
    "roles/monitoring.metricWriter",      # Write metrics
    "roles/logging.logWriter",            # Write logs
  ])

  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.gke_workload.email}"
}

# Outputs
output "platform_dev_service_account" {
  value = {
    email      = google_service_account.platform_dev.email
    account_id = google_service_account.platform_dev.account_id
  }
  description = "Platform development service account details"
}

output "gke_workload_service_account" {
  value = {
    email      = google_service_account.gke_workload.email
    account_id = google_service_account.gke_workload.account_id
  }
  description = "GKE workload identity service account details"
}

output "enabled_apis" {
  value       = [for api in google_project_service.required_apis : api.service]
  description = "List of enabled GCP APIs"
}
