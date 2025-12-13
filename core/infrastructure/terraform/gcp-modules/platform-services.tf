# Platform Services - Cloud Run deployments with Confluent Cloud Kafka
# Web Services Only: product-generator, discovery-agent
# NOTE: product-service, stream-analysis, ml-consumer, event-producer commented out (need fixes)

# =============================================================================
# DATA SOURCES - Confluent Cloud Secrets
# =============================================================================

data "google_secret_manager_secret_version" "confluent_bootstrap" {
  secret = "confluent-bootstrap-server"
}

data "google_secret_manager_secret_version" "confluent_kafka_key" {
  secret = "confluent-kafka-api-key"
}

data "google_secret_manager_secret_version" "confluent_kafka_secret" {
  secret = "confluent-kafka-api-secret"
}

data "google_secret_manager_secret_version" "confluent_sr_url" {
  secret = "confluent-schema-registry-url"
}

data "google_secret_manager_secret_version" "confluent_sr_key" {
  secret = "confluent-sr-api-key"
}

data "google_secret_manager_secret_version" "confluent_sr_secret" {
  secret = "confluent-sr-api-secret"
}

# =============================================================================
# LOCALS
# =============================================================================

locals {
  image_registry = "${var.region}-docker.pkg.dev/${var.project_id}/ai-platform-repo"
  
  # Common Kafka environment variables for all services
  kafka_env = {
    KAFKA_BOOTSTRAP_SERVERS    = data.google_secret_manager_secret_version.confluent_bootstrap.secret_data
    KAFKA_SECURITY_PROTOCOL    = "SASL_SSL"
    KAFKA_SASL_MECHANISM       = "PLAIN"
    KAFKA_SASL_USERNAME        = data.google_secret_manager_secret_version.confluent_kafka_key.secret_data
    KAFKA_SASL_PASSWORD        = data.google_secret_manager_secret_version.confluent_kafka_secret.secret_data
    SCHEMA_REGISTRY_URL        = data.google_secret_manager_secret_version.confluent_sr_url.secret_data
    SCHEMA_REGISTRY_API_KEY    = data.google_secret_manager_secret_version.confluent_sr_key.secret_data
    SCHEMA_REGISTRY_API_SECRET = data.google_secret_manager_secret_version.confluent_sr_secret.secret_data
  }
}

# =============================================================================
# SERVICE: product-generator
# AI-powered product creation agent (FastAPI on port 8003)
# =============================================================================

resource "google_cloud_run_v2_service" "product_generator" {
  name     = "product-generator"
  location = var.region
  
  deletion_protection = false
  
  template {
    containers {
      image = "${local.image_registry}/product-generator:latest"
      
      ports {
        container_port = 8003
      }
      
      resources {
        limits = {
          cpu    = "1"
          memory = "1Gi"
        }
      }
      
      # Kafka configuration
      dynamic "env" {
        for_each = local.kafka_env
        content {
          name  = env.key
          value = env.value
        }
      }
      
      # AI configuration
      env {
        name  = "ANTHROPIC_API_KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.anthropic_key.secret_id
            version = "latest"
          }
        }
      }
      
      env {
        name  = "ENVIRONMENT"
        value = "production"
      }
    }
    
    scaling {
      min_instance_count = 0
      max_instance_count = 10
    }
    
    vpc_access {
      network_interfaces {
        network    = google_compute_network.vpc.name
        subnetwork = google_compute_subnetwork.subnet.name
      }
      egress = "ALL_TRAFFIC"
    }
  }
  
  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }
}

resource "google_cloud_run_v2_service_iam_member" "product_generator_public" {
  name     = google_cloud_run_v2_service.product_generator.name
  location = var.region
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# =============================================================================
# SERVICE: discovery-agent
# AI agent for service discovery and orchestration (FastAPI on port 8004)
# =============================================================================

resource "google_cloud_run_v2_service" "discovery_agent" {
  name     = "discovery-agent"
  location = var.region
  
  deletion_protection = false
  
  template {
    containers {
      image = "${local.image_registry}/discovery-agent:latest"
      
      ports {
        container_port = 8004
      }
      
      resources {
        limits = {
          cpu    = "1"
          memory = "1Gi"
        }
      }
      
      # Kafka configuration
      dynamic "env" {
        for_each = local.kafka_env
        content {
          name  = env.key
          value = env.value
        }
      }
      
      # AI configuration
      env {
        name  = "ANTHROPIC_API_KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.anthropic_key.secret_id
            version = "latest"
          }
        }
      }
      
      env {
        name  = "ENVIRONMENT"
        value = "production"
      }
    }
    
    scaling {
      min_instance_count = 0
      max_instance_count = 10
    }
    
    vpc_access {
      network_interfaces {
        network    = google_compute_network.vpc.name
        subnetwork = google_compute_subnetwork.subnet.name
      }
      egress = "ALL_TRAFFIC"
    }
  }
  
  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }
}

resource "google_cloud_run_v2_service_iam_member" "discovery_agent_public" {
  name     = google_cloud_run_v2_service.discovery_agent.name
  location = var.region
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# =============================================================================
# OUTPUTS
# =============================================================================

output "product_generator_url" {
  description = "Product Generator URL"
  value       = google_cloud_run_v2_service.product_generator.uri
}

output "discovery_agent_url" {
  description = "Discovery Agent URL"
  value       = google_cloud_run_v2_service.discovery_agent.uri
}

# =============================================================================
# TODO: Add these services after fixing their Docker images
# =============================================================================
# - product-service: Needs Dockerfile at templates/supply-chain/services/product-service
# - stream-analysis: Background worker - needs HTTP health endpoint added
# - ml-consumer: Background worker - port 8000 in Docker, needs alignment
# - event-producer: Background worker - no HTTP server, needs health endpoint
