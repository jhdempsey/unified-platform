# Platform Infrastructure - Development Environment

terraform {
  required_version = ">= 1.5.0"
  
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
    google-beta = {
      source  = "hashicorp/google-beta"
      version = "~> 5.0"
    }
  }

  # Optional: Remote state
  # backend "gcs" {
  #   bucket = "platform-terraform-state-dev"
  #   prefix = "dev/terraform/state"
  # }
}

# Provider configuration
provider "google" {
  project = var.project_id
  region  = var.region
}

provider "google-beta" {
  project = var.project_id
  region  = var.region
}

# Use project module
module "project" {
  source = "../../modules/project"

  project_id      = var.project_id
  environment     = var.environment
  project_labels  = var.project_labels
}

# Use secrets module
module "secrets" {
  source = "../../modules/secrets"

  project_id        = var.project_id
  environment       = var.environment
  secrets_to_create = var.secrets_to_create
  project_labels    = var.project_labels
  
  # Pass service accounts from project module
  gke_workload_sa_email = module.project.gke_workload_service_account.email

  depends_on = [module.project]
}

# Future: Uncomment when ready to deploy
# module "network" {
#   source = "../../modules/network"
#   
#   project_id     = var.project_id
#   environment    = var.environment
#   vpc_name       = var.vpc_name
#   subnet_cidr    = var.subnet_cidr
#   project_labels = var.project_labels
# }

# module "gke" {
#   source = "../../modules/gke"
#   
#   project_id        = var.project_id
#   region            = var.region
#   environment       = var.environment
#   cluster_name      = var.gke_cluster_name
#   node_count        = var.gke_node_count
#   machine_type      = var.gke_machine_type
#   preemptible       = var.gke_preemptible
#   network_name      = module.network.network_name
#   subnet_name       = module.network.subnet_name
#   
#   depends_on = [module.network]
# }
