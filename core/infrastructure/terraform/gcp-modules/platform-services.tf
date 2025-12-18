# Platform Services - Cloud Run deployments with Confluent Cloud Kafka
# Services: product-generator, discovery-agent, product-service, event-producer, stream-analysis

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
      # Redis/Memorystore configuration
      env {
        name  = "REDIS_HOST"
        value = google_redis_instance.cache.host
      }
      
      env {
        name  = "REDIS_PORT"
        value = "6379"
      }
      
      env {
        name  = "REDIS_URL"
        value = "redis://${google_redis_instance.cache.host}:6379"
      }
    }
    
    scaling {
      min_instance_count = 1
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
      
      # Service URLs for inter-service communication
      env {
        name  = "PRODUCT_SERVICE_URL"
        value = "https://product-service-${data.google_project.project.number}.${var.region}.run.app"
      }
    }
    
    scaling {
      min_instance_count = 1
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

# Data source for project number (needed for Cloud Run URLs)
data "google_project" "project" {
  project_id = var.project_id
}

resource "google_cloud_run_v2_service_iam_member" "discovery_agent_public" {
  name     = google_cloud_run_v2_service.discovery_agent.name
  location = var.region
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# =============================================================================
# SERVICE: product-service
# Product CRUD REST API (FastAPI on port 8001)
# =============================================================================

resource "google_cloud_run_v2_service" "product_service" {
  name     = "product-service"
  location = var.region
  
  deletion_protection = false
  
  template {
    containers {
      image = "${local.image_registry}/product-service:latest"
      
      ports {
        container_port = 8001
      }
      
      resources {
        limits = {
          cpu    = "1"
          memory = "512Mi"
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
      
      # Database configuration (Cloud SQL)
      env {
        name  = "DATABASE_URL"
        value = "postgresql://mlflow:${random_password.mlflow_db_password.result}@/mlflow?host=/cloudsql/${var.project_id}:${var.region}:mlflow-db"
      }
      
      env {
        name  = "ENVIRONMENT"
        value = "production"
      }
      
      # Cloud SQL connection
      volume_mounts {
        name       = "cloudsql"
        mount_path = "/cloudsql"
      }
    }
    
    volumes {
      name = "cloudsql"
      cloud_sql_instance {
        instances = ["${var.project_id}:${var.region}:mlflow-db"]
      }
    }
    
    scaling {
      min_instance_count = 1
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

resource "google_cloud_run_v2_service_iam_member" "product_service_public" {
  name     = google_cloud_run_v2_service.product_service.name
  location = var.region
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# =============================================================================
# SERVICE: event-producer
# Produces test events to Kafka (FastAPI on port 8080)
# =============================================================================

resource "google_cloud_run_v2_service" "event_producer" {
  name     = "event-producer"
  location = var.region
  
  deletion_protection = false
  
  template {
    containers {
      image = "${local.image_registry}/event-producer:latest"
      
      ports {
        container_port = 8080
      }
      
      resources {
        limits = {
          cpu    = "1"
          memory = "512Mi"
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
      
      env {
        name  = "ENVIRONMENT"
        value = "production"
      }
    }
    
    scaling {
      min_instance_count = 1
      max_instance_count = 3
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

resource "google_cloud_run_v2_service_iam_member" "event_producer_public" {
  name     = google_cloud_run_v2_service.event_producer.name
  location = var.region
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# =============================================================================
# SERVICE: stream-analysis
# AI-powered stream quality analysis (FastAPI on port 8080)
# =============================================================================

resource "google_cloud_run_v2_service" "stream_analysis" {
  name     = "stream-analysis"
  location = var.region
  
  deletion_protection = false
  
  template {
    containers {
      image = "${local.image_registry}/stream-analysis:latest"
      
      ports {
        container_port = 8080
      }
      
      resources {
        limits = {
          cpu    = "2"
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
      
      # Topics to monitor
      env {
        name  = "KAFKA_TOPICS"
        value = "supply-chain.orders,supply-chain.predictions,supply-chain.alerts,order-events,product-events,supplier-events"
      }
    }
    
    scaling {
      min_instance_count = 1  # Keep running for continuous consumption
      max_instance_count = 5
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

resource "google_cloud_run_v2_service_iam_member" "stream_analysis_public" {
  name     = google_cloud_run_v2_service.stream_analysis.name
  location = var.region
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# =============================================================================
# SERVICE: ml-consumer
# ML predictions consumer (FastAPI on port 8080)
# =============================================================================

resource "google_cloud_run_v2_service" "ml_consumer" {
  name     = "ml-consumer"
  location = var.region
  
  deletion_protection = false
  
  template {
    containers {
      image = "${local.image_registry}/ml-consumer:latest"
      
      ports {
        container_port = 8080
      }
      
      resources {
        limits = {
          cpu    = "2"
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
      
      env {
        name  = "ENVIRONMENT"
        value = "production"
      }

      # Redis/Memorystore configuration
      env {
        name  = "REDIS_HOST"
        value = google_redis_instance.cache.host
      }

      env {
        name  = "REDIS_PORT"
        value = "6379"
      }

      env {
        name  = "REDIS_URL"
        value = "redis://${google_redis_instance.cache.host}:6379"
      }
    }
    
    scaling {
      min_instance_count = 1  # Keep running for continuous consumption
      max_instance_count = 5
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

resource "google_cloud_run_v2_service_iam_member" "ml_consumer_public" {
  name     = google_cloud_run_v2_service.ml_consumer.name
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

output "product_service_url" {
  description = "Product Service URL"
  value       = google_cloud_run_v2_service.product_service.uri
}

output "event_producer_url" {
  description = "Event Producer URL"
  value       = google_cloud_run_v2_service.event_producer.uri
}

output "stream_analysis_url" {
  description = "Stream Analysis URL"
  value       = google_cloud_run_v2_service.stream_analysis.uri
}

output "ml_consumer_url" {
  description = "ML Consumer URL"
  value       = google_cloud_run_v2_service.ml_consumer.uri
}

# =============================================================================
# SERVICE: model-inference
# ML model serving with scikit-learn Random Forest (FastAPI on port 8001)
# =============================================================================

resource "google_cloud_run_v2_service" "model_inference" {
  name     = "model-inference"
  location = var.region
  
  deletion_protection = false
  
  template {
    containers {
      image = "${local.image_registry}/model-inference:latest"
      
      ports {
        container_port = 8001
      }
      
      resources {
        limits = {
          cpu    = "2"
          memory = "2Gi"
        }
      }
      
      env {
        name  = "ENVIRONMENT"
        value = "production"
      }
      
      env {
        name  = "MLFLOW_TRACKING_URI"
        value = google_cloud_run_v2_service.mlflow.uri
      }
    }
    
    scaling {
      min_instance_count = 1
      max_instance_count = 5
    }
  }
  
  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }
}

resource "google_cloud_run_v2_service_iam_member" "model_inference_public" {
  name     = google_cloud_run_v2_service.model_inference.name
  location = var.region
  role     = "roles/run.invoker"
  member   = "allUsers"
}

output "model_inference_url" {
  description = "Model Inference URL"
  value       = google_cloud_run_v2_service.model_inference.uri
}
