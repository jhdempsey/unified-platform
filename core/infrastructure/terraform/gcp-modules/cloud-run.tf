# terraform/cloud-run.tf

# RAG Service
resource "google_cloud_run_service" "rag_service" {
  name     = "rag-service"
  location = var.region
  project  = var.project_id

  template {
    spec {
      service_account_name = google_service_account.mlflow.email

      containers {
        image = "${var.region}-docker.pkg.dev/${var.project_id}/cloud-run-source-deploy/rag-service:latest"

        env {
          name  = "GCP_PROJECT_ID"
          value = var.project_id
        }

        # Reference Secret Manager secret
        env {
          name = "PINECONE_API_KEY"
          value_from {
            secret_key_ref {
              name = "pinecone-api-key"
              key  = "latest"
            }
          }
        }

        resources {
          limits = {
            cpu    = "1000m"
            memory = "1Gi"
          }
        }
      }

      container_concurrency = 80
      timeout_seconds       = 300
    }

    metadata {
      annotations = {
        "autoscaling.knative.dev/maxScale"      = "100"
        "autoscaling.knative.dev/minScale"      = "1"
        "run.googleapis.com/client-name"        = "terraform"
      }
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }

  autogenerate_revision_name = true

  depends_on = [
    google_service_account.mlflow
  ]
}

# data "kubernetes_service" "ml_consumer" {
#   metadata {
#     name      = "ml-consumer"
#     namespace = "default"
#   }
#   depends_on = [kubernetes_service.ml_consumer]
# }

# Allow public access
resource "google_cloud_run_service_iam_member" "rag_public" {
  service  = google_cloud_run_service.rag_service.name
  location = google_cloud_run_service.rag_service.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# Artifact registry for dashboard images
resource "google_artifact_registry_repository" "ai_platform_repo" {
  location      = var.region
  repository_id = "ai-platform-repo"
  description   = "Docker images for Dashboard service"
  format        = "DOCKER"
}

# Dashboard Service - Updated with Cloud Run URLs
resource "google_cloud_run_service" "dashboard" {
  name     = "dashboard"
  location = var.region
  project  = var.project_id

  template {
    spec {
      containers {
        image = "${var.region}-docker.pkg.dev/${var.project_id}/cloud-run-source-deploy/dashboard:latest"

        # Cloud Run service URLs
        env {
          name  = "ENVIRONMENT"
          value = "production"
        }
        
        env {
          name  = "RAG_SERVICE_URL"
          value = google_cloud_run_service.rag_service.status[0].url
        }
        
        env {
          name  = "AI_GATEWAY_URL"
          value = "https://ai-gateway-${data.google_project.project.number}.${var.region}.run.app"
        }
        
        env {
          name  = "AI_GATEWAY_UI_URL"
          value = "https://ai-gateway-${data.google_project.project.number}.${var.region}.run.app"
        }
        
        env {
          name  = "DISCOVERY_AGENT_URL"
          value = "https://discovery-agent-${data.google_project.project.number}.${var.region}.run.app"
        }
        
        env {
          name  = "DISCOVERY_AGENT_UI_URL"
          value = "https://discovery-agent-${data.google_project.project.number}.${var.region}.run.app"
        }
        
        env {
          name  = "PRODUCT_SERVICE_URL"
          value = "https://product-service-${data.google_project.project.number}.${var.region}.run.app"
        }
        
        env {
          name  = "ML_CONSUMER_URL"
          value = google_cloud_run_v2_service.model_inference.uri
        }
        
        env {
          name  = "ML_CONSUMER_METRICS_URL"
          value = google_cloud_run_v2_service.model_inference.uri
        }
        
        env {
          name  = "STREAM_ANALYSIS_URL"
          value = "https://stream-analysis-${data.google_project.project.number}.${var.region}.run.app"
        }
        
        env {
          name  = "EVENT_PRODUCER_URL"
          value = "https://event-producer-${data.google_project.project.number}.${var.region}.run.app"
        }
        
        env {
          name  = "BACKSTAGE_URL"
          value = "https://backstage-${data.google_project.project.number}.${var.region}.run.app"
        }
        
        env {
          name  = "MLFLOW_TRACKING_URI"
          value = google_cloud_run_v2_service.mlflow.uri
        }
        
        env {
          name  = "MLFLOW_UI_URL"
          value = google_cloud_run_v2_service.mlflow.uri
        }
        
        # Model Inference uses ML Consumer
        env {
          name  = "MODEL_INFERENCE_URL"
          value = google_cloud_run_v2_service.model_inference.uri
        }
        
        env {
          name  = "MODEL_INFERENCE_UI_URL"
          value = google_cloud_run_v2_service.model_inference.uri
        }
        
        # Kafka UI - Confluent Cloud
        env {
          name  = "KAFKA_UI_URL"
          value = "https://confluent.cloud"
        }

        resources {
          limits = {
            cpu    = "1000m"
            memory = "512Mi"
          }
        }
      }

      container_concurrency = 80
      timeout_seconds       = 300
    }

    metadata {
      annotations = {
        "autoscaling.knative.dev/maxScale" = "100"
        "autoscaling.knative.dev/minScale" = "0"
        "run.googleapis.com/client-name"   = "terraform"
      }
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }

  autogenerate_revision_name = true

  depends_on = [
    google_project_service.required_apis
  ]
}


# Allow public access to dashboard
resource "google_cloud_run_service_iam_member" "dashboard_public" {
  service  = google_cloud_run_service.dashboard.name
  location = google_cloud_run_service.dashboard.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# Data sources for K8s service IPs
# data "kubernetes_service" "mlflow" {
#   metadata {
#     name = "mlflow"
#   }
# }
# 
# data "kubernetes_service" "model_inference" {
#   metadata {
#     name = "model-inference"
#   }
# }
# 
# Outputs
output "rag_service_url" {
  value       = google_cloud_run_service.rag_service.status[0].url
  description = "RAG Service URL"
}

output "dashboard_url" {
  value       = google_cloud_run_service.dashboard.status[0].url
  description = "Dashboard URL"
}
