# ==============================================================================
# MCP SERVER - Model Context Protocol Server
# ==============================================================================
# Provides standardized tool interface for AI agents
# Implements MCP protocol for framework-agnostic agent integration

resource "google_cloud_run_service" "mcp_server" {
  name     = "mcp-server"
  location = var.region
  project  = var.project_id

  template {
    spec {
      containers {
        image = "${var.region}-docker.pkg.dev/${var.project_id}/ai-platform/mcp-server:latest"

        env {
          name  = "RAG_SERVICE_URL"
          value = google_cloud_run_service.rag_service.status[0].url
        }

        resources {
          limits = {
            cpu    = "1000m"
            memory = "512Mi"
          }
        }

        ports {
          container_port = 8080
        }
      }

      container_concurrency = 80
      timeout_seconds       = 300
    }

    metadata {
      annotations = {
        "autoscaling.knative.dev/maxScale" = "10"
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
    google_cloud_run_service.rag_service
  ]
}

# Allow public access (Phase 1 MVP - add authentication in Phase 2)
resource "google_cloud_run_service_iam_member" "mcp_server_public" {
  service  = google_cloud_run_service.mcp_server.name
  location = google_cloud_run_service.mcp_server.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# Output
output "mcp_server_url" {
  value       = google_cloud_run_service.mcp_server.status[0].url
  description = "MCP Server URL for agent integration"
}
