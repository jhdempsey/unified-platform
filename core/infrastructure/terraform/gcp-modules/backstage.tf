# =============================================================================
# Backstage Developer Portal - Cloud Run
# =============================================================================

resource "google_cloud_run_v2_service" "backstage" {
  name     = "backstage"
  location = var.region
  
  deletion_protection = false
  
  template {
    containers {
      image = "${local.image_registry}/backstage:latest"
      
      ports {
        container_port = 8080
      }
      
      resources {
        limits = {
          cpu    = "2"
          memory = "2Gi"
        }
      }
      
      env {
        name  = "NODE_ENV"
        value = "production"
      }
    }
    
    scaling {
      min_instance_count = 0
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

resource "google_cloud_run_v2_service_iam_member" "backstage_public" {
  name     = google_cloud_run_v2_service.backstage.name
  location = var.region
  role     = "roles/run.invoker"
  member   = "allUsers"
}

output "backstage_url" {
  description = "Backstage Developer Portal URL"
  value       = google_cloud_run_v2_service.backstage.uri
}
