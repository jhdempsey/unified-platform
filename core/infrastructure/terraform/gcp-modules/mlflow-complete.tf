# ============================================================================
# MLflow Infrastructure - Using Default Network (Works!)
# ============================================================================

# Enable required APIs
resource "google_project_service" "sql_admin" {
  service            = "sqladmin.googleapis.com"
  disable_on_destroy = false
}

# ============================================================================
# MLflow Database Password Management
# ============================================================================

# Generate secure random password WITHOUT special characters
resource "random_password" "mlflow_db_password" {
  length  = 32
  special = false # No special characters to avoid URL encoding issues
  upper   = true
  lower   = true
  numeric = true
}

# Store in Secret Manager
resource "google_secret_manager_secret" "mlflow_db_password" {
  secret_id = "mlflow-db-password"

  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_version" "mlflow_db_password" {
  secret      = google_secret_manager_secret.mlflow_db_password.id
  secret_data = random_password.mlflow_db_password.result
}

# ============================================================================
# Cloud SQL PostgreSQL Instance on DEFAULT network
# (Uses existing service networking peering)
# ============================================================================

resource "google_sql_database_instance" "mlflow" {
  name                = "mlflow-db"
  database_version    = "POSTGRES_15"
  region              = var.region
  deletion_protection = false

  settings {
    tier              = var.mlflow_db_tier
    availability_type = "ZONAL"
    disk_type         = "PD_SSD"
    disk_size         = 10
    disk_autoresize   = true

    backup_configuration {
      enabled    = true
      start_time = "03:00"
    }

    maintenance_window {
      day  = 7
      hour = 4
    }

    ip_configuration {
      # Temporary: enable public IP for initial setup
      ipv4_enabled    = true
      private_network = "projects/${var.project_id}/global/networks/default"
      ssl_mode        = "ALLOW_UNENCRYPTED_AND_ENCRYPTED"
    }
  }

  depends_on = [google_project_service.sql_admin]
}

# Create MLflow database
resource "google_sql_database" "mlflow" {
  name     = "mlflow"
  instance = google_sql_database_instance.mlflow.name
}

# Create MLflow database user
resource "google_sql_user" "mlflow" {
  name     = "mlflow"
  instance = google_sql_database_instance.mlflow.name
  password = random_password.mlflow_db_password.result
}

# ============================================================================
# Kubernetes Secret for MLflow
# ============================================================================

resource "kubernetes_secret" "mlflow_db" {
  metadata {
    name      = "mlflow-db-secret"
    namespace = "default"
  }

  data = {
    db-password       = random_password.mlflow_db_password.result
    db-host           = google_sql_database_instance.mlflow.private_ip_address
    db-name           = google_sql_database.mlflow.name
    db-user           = google_sql_user.mlflow.name
    connection-string = "postgresql://${google_sql_user.mlflow.name}:${random_password.mlflow_db_password.result}@${google_sql_database_instance.mlflow.private_ip_address}:5432/${google_sql_database.mlflow.name}"
  }

  type = "Opaque"

  depends_on = [
    google_container_cluster.primary,
    google_sql_database_instance.mlflow,
    google_sql_database.mlflow,
    google_sql_user.mlflow
  ]
}

# ============================================================================
# Outputs
# ============================================================================

output "mlflow_db_private_ip" {
  value       = google_sql_database_instance.mlflow.private_ip_address
  description = "Private IP address of MLflow Cloud SQL instance"
}

output "mlflow_connection_string" {
  value       = "postgresql://mlflow:***@${google_sql_database_instance.mlflow.private_ip_address}:5432/mlflow"
  description = "MLflow database connection string (password redacted)"
}

output "mlflow_db_password" {
  value       = random_password.mlflow_db_password.result
  description = "MLflow database password"
  sensitive   = true
}

output "mlflow_db_connection_name" {
  value       = google_sql_database_instance.mlflow.connection_name
  description = "Cloud SQL connection name"
}
