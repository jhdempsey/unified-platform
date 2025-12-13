# =============================================================================
# CLOUD NAT - Outbound Internet Access for VPC-connected services
# =============================================================================
# Required for Cloud Run services in VPC to reach external endpoints
# like Confluent Cloud (Azure) while keeping services private
# =============================================================================

# Cloud Router (required for NAT)
resource "google_compute_router" "router" {
  name    = "ai-platform-router"
  region  = var.region
  network = google_compute_network.vpc.id
  project = var.project_id
}

# Cloud NAT for outbound internet access
resource "google_compute_router_nat" "nat" {
  name                               = "ai-platform-nat"
  router                             = google_compute_router.router.name
  region                             = var.region
  project                            = var.project_id
  nat_ip_allocate_option             = "AUTO_ONLY"
  source_subnetwork_ip_ranges_to_nat = "ALL_SUBNETWORKS_ALL_IP_RANGES"
  
  log_config {
    enable = true
    filter = "ERRORS_ONLY"
  }
}

# =============================================================================
# OUTPUTS
# =============================================================================

output "cloud_nat_name" {
  description = "Cloud NAT gateway name"
  value       = google_compute_router_nat.nat.name
}

output "cloud_router_name" {
  description = "Cloud Router name"
  value       = google_compute_router.router.name
}
