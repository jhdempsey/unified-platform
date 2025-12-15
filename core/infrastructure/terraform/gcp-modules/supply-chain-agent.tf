# =============================================================================
# Supply Chain AI Agent - Cloud Run
# Replaces Agent Builder with fully-automated custom agent
# =============================================================================

resource "google_cloud_run_v2_service" "supply_chain_agent" {
  name     = "supply-chain-agent"
  location = var.region
  
  deletion_protection = false
  
  template {
    containers {
      image = "${local.image_registry}/supply-chain-agent:latest"
      
      ports {
        container_port = 8080
      }
      
      resources {
        limits = {
          cpu    = "1"
          memory = "512Mi"
        }
      }
      
      # Anthropic API Key
      env {
        name = "ANTHROPIC_API_KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.anthropic_key.secret_id
            version = "latest"
          }
        }
      }
      
      # Service URLs
      env {
        name  = "RAG_SERVICE_URL"
        value = google_cloud_run_service.rag_service.status[0].url
      }
      
      env {
        name  = "PRODUCT_SERVICE_URL"
        value = "https://product-service-${data.google_project.project.number}.${var.region}.run.app"
      }
      
      env {
        name  = "DISCOVERY_AGENT_URL"
        value = "https://discovery-agent-${data.google_project.project.number}.${var.region}.run.app"
      }
      
      env {
        name  = "PRODUCT_GENERATOR_URL"
        value = "https://product-generator-${data.google_project.project.number}.${var.region}.run.app"
      }
      
      env {
        name  = "STREAM_ANALYSIS_URL"
        value = "https://stream-analysis-${data.google_project.project.number}.${var.region}.run.app"
      }
      
      env {
        name  = "ML_CONSUMER_URL"
        value = "https://ml-consumer-${data.google_project.project.number}.${var.region}.run.app"
      }
    }
    
    scaling {
      min_instance_count = 0
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

resource "google_cloud_run_v2_service_iam_member" "supply_chain_agent_public" {
  name     = google_cloud_run_v2_service.supply_chain_agent.name
  location = var.region
  role     = "roles/run.invoker"
  member   = "allUsers"
}

output "supply_chain_agent_url" {
  description = "Supply Chain AI Agent URL"
  value       = google_cloud_run_v2_service.supply_chain_agent.uri
}
