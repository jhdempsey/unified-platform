# output "gke_cluster_name" {
#   description = "GKE Cluster name"
#   value       = google_container_cluster.primary.name
# }
# output "gke_cluster_endpoint" {
#   description = "GKE Cluster endpoint"
#   value       = google_container_cluster.primary.endpoint
#   sensitive   = true
# }
output "ai_gateway_url" {
  description = "AI Gateway Cloud Run URL"
  value       = google_cloud_run_v2_service.ai_gateway.uri
}
output "redis_host" {
  description = "Redis host"
  value       = google_redis_instance.cache.host
}
output "redis_port" {
  description = "Redis port"
  value       = google_redis_instance.cache.port
}
output "models_bucket" {
  description = "GCS bucket for models"
  value       = google_storage_bucket.models.name
}
# output "configure_kubectl" {
#   description = "Command to configure kubectl"
#   value       = "gcloud container clusters get-credentials ${google_container_cluster.primary.name} --region ${var.region} --project ${var.project_id}"
# }
