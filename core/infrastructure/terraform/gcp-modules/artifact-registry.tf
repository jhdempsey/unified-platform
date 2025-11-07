# ============================================================================
# Artifact Registry for Docker Images
# ============================================================================

# Enable Artifact Registry API
resource "google_project_service" "artifact_registry" {
  service            = "artifactregistry.googleapis.com"
  disable_on_destroy = false
}

# Create Artifact Registry repository
resource "google_artifact_registry_repository" "ai_platform" {
  location      = var.region
  repository_id = "ai-platform"
  description   = "Docker images for AI Platform services"
  format        = "DOCKER"

  depends_on = [google_project_service.artifact_registry]
}

# Output the repository URL
output "artifact_registry_url" {
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.ai_platform.repository_id}"
  description = "Artifact Registry repository URL for docker push"
}
