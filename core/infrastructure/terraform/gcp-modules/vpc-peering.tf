# ============================================================================
# VPC Network Peering - Connect ai-platform-vpc to default network
# ============================================================================

# Peering from ai-platform-vpc to default
resource "google_compute_network_peering" "ai_platform_to_default" {
  name         = "ai-platform-to-default"
  network      = google_compute_network.vpc.self_link
  peer_network = "projects/${var.project_id}/global/networks/default"

  export_custom_routes = true
  import_custom_routes = true
}

# Peering from default to ai-platform-vpc (bidirectional)
resource "google_compute_network_peering" "default_to_ai_platform" {
  name         = "default-to-ai-platform"
  network      = "projects/${var.project_id}/global/networks/default"
  peer_network = google_compute_network.vpc.self_link

  export_custom_routes = true
  import_custom_routes = true
}
