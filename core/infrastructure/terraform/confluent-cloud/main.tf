# =============================================================================
# Confluent Cloud Terraform - Import Existing Resources
# Use this when you already have a Kafka cluster in Confluent Cloud
# =============================================================================

terraform {
  required_providers {
    confluent = {
      source  = "confluentinc/confluent"
      version = "~> 1.83"
    }
  }
}

# =============================================================================
# PROVIDER CONFIGURATION
# =============================================================================

provider "confluent" {
  cloud_api_key    = var.confluent_cloud_api_key
  cloud_api_secret = var.confluent_cloud_api_secret
}

# =============================================================================
# VARIABLES
# =============================================================================

variable "confluent_cloud_api_key" {
  description = "Confluent Cloud API Key"
  type        = string
  sensitive   = true
}

variable "confluent_cloud_api_secret" {
  description = "Confluent Cloud API Secret"
  type        = string
  sensitive   = true
}

# IDs of your existing resources (get from Confluent Cloud UI)
variable "existing_environment_id" {
  description = "Existing Confluent Environment ID (e.g., env-xxxxx)"
  type        = string
}

variable "existing_kafka_cluster_id" {
  description = "Existing Kafka Cluster ID (e.g., lkc-xxxxx)"
  type        = string
}

variable "existing_schema_registry_id" {
  description = "Existing Schema Registry Cluster ID (e.g., lsrc-xxxxx)"
  type        = string
  default     = ""  # Optional - leave empty if not using
}

variable "cloud_provider" {
  description = "Cloud provider"
  type        = string
  default     = "AZURE"
}

variable "cloud_region" {
  description = "Cloud region"
  type        = string
  default     = "eastus"
}

variable "flink_max_cfu" {
  description = "Maximum CFUs for Flink compute pool"
  type        = number
  default     = 5
}

# Existing API credentials (from your current setup)
variable "existing_kafka_api_key" {
  description = "Existing Kafka API Key"
  type        = string
  sensitive   = true
}

variable "existing_kafka_api_secret" {
  description = "Existing Kafka API Secret"
  type        = string
  sensitive   = true
}

# =============================================================================
# REFERENCE EXISTING RESOURCES (Data Sources)
# =============================================================================

data "confluent_environment" "existing" {
  id = var.existing_environment_id
}

data "confluent_kafka_cluster" "existing" {
  id = var.existing_kafka_cluster_id
  
  environment {
    id = data.confluent_environment.existing.id
  }
}

# Schema Registry lookup disabled - use existing setup
# data "confluent_schema_registry_cluster" "existing" {
#   count = var.existing_schema_registry_id != "" ? 1 : 0
#   id    = var.existing_schema_registry_id
#   
#   environment {
#     id = data.confluent_environment.existing.id
#   }
# }

data "confluent_organization" "main" {}

data "confluent_flink_region" "main" {
  cloud  = var.cloud_provider
  region = var.cloud_region
}

# =============================================================================
# SERVICE ACCOUNT FOR FLINK (New)
# =============================================================================

resource "confluent_service_account" "flink" {
  display_name = "unified-platform-flink"
  description  = "Service account for Flink compute pool"
}

# =============================================================================
# FLINK COMPUTE POOL (New)
# =============================================================================

resource "confluent_flink_compute_pool" "main" {
  display_name = "unified-platform-flink"
  cloud        = var.cloud_provider
  region       = var.cloud_region
  max_cfu      = var.flink_max_cfu

  environment {
    id = data.confluent_environment.existing.id
  }
}

# Role binding for Flink to access Kafka
resource "confluent_role_binding" "flink_kafka" {
  principal   = "User:${confluent_service_account.flink.id}"
  role_name   = "CloudClusterAdmin"
  crn_pattern = data.confluent_kafka_cluster.existing.rbac_crn
}

# =============================================================================
# KAFKA TOPICS
# Topics already exist - not managed by Terraform
# To manage topics via Terraform, uncomment and import:
#   terraform import confluent_kafka_topic.order_events lkc-xxxxx/order-events
# =============================================================================

# =============================================================================
# OUTPUTS
# =============================================================================

output "environment_id" {
  description = "Confluent Environment ID"
  value       = data.confluent_environment.existing.id
}

output "kafka_cluster_id" {
  description = "Kafka Cluster ID"
  value       = data.confluent_kafka_cluster.existing.id
}

output "kafka_bootstrap_server" {
  description = "Kafka Bootstrap Server"
  value       = data.confluent_kafka_cluster.existing.bootstrap_endpoint
}

output "flink_compute_pool_id" {
  description = "Flink Compute Pool ID"
  value       = confluent_flink_compute_pool.main.id
}

output "flink_service_account_id" {
  description = "Flink Service Account ID"
  value       = confluent_service_account.flink.id
}

output "flink_sql_workspace_url" {
  description = "URL to Flink SQL Workspace in Confluent Cloud"
  value       = "https://confluent.cloud/environments/${data.confluent_environment.existing.id}/flink/workspaces"
}

output "next_steps" {
  description = "Next steps after Terraform apply"
  value       = <<-EOT
    
    ✅ Terraform has created:
    1. Flink compute pool: ${confluent_flink_compute_pool.main.display_name}
    2. Flink service account with Kafka access
    
    📋 Next steps:
    1. Go to Flink SQL Workspace:
       https://confluent.cloud/environments/${data.confluent_environment.existing.id}/flink/workspaces
    2. Select compute pool: unified-platform-flink
    3. Create Flink SQL tables for your source topics
    4. Run stream processing queries
    
    See docs/CONFLUENT_FLINK_SETUP.md for SQL statements.
  EOT
}
