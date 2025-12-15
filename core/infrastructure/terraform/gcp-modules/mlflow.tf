# =============================================================================
# MLflow Tracking Server - Cloud Run
# =============================================================================

resource "google_cloud_run_v2_service" "mlflow" {
  name     = "mlflow"
  location = var.region
  
  deletion_protection = false
  
  template {
    containers {
      image = "${local.image_registry}/mlflow:latest"
      
      ports {
        container_port = 8080
      }
      
      resources {
        limits = {
          cpu    = "1"
          memory = "1Gi"
        }
      }
      
      # MLflow configuration
      env {
        name  = "MLFLOW_BACKEND_STORE_URI"
        value = "postgresql://mlflow:${random_password.mlflow_db_password.result}@/mlflow?host=/cloudsql/${google_sql_database_instance.mlflow.connection_name}"
      }
      
      env {
        name  = "MLFLOW_ARTIFACT_ROOT"
        value = "gs://${google_storage_bucket.models.name}/mlflow-artifacts"
      }
      
      env {
        name  = "MLFLOW_HOST"
        value = "0.0.0.0"
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
        instances = [google_sql_database_instance.mlflow.connection_name]
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
  
  depends_on = [
    google_sql_database_instance.mlflow,
    google_storage_bucket.models
  ]
}

resource "google_cloud_run_v2_service_iam_member" "mlflow_public" {
  name     = google_cloud_run_v2_service.mlflow.name
  location = var.region
  role     = "roles/run.invoker"
  member   = "allUsers"
}

output "mlflow_url" {
  description = "MLflow Tracking Server URL"
  value       = google_cloud_run_v2_service.mlflow.uri
}
