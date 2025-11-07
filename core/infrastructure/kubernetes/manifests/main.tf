terraform {
  required_version = ">= 1.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }

  backend "local" {
    path = "terraform.tfstate"
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# Enable required APIs
resource "google_project_service" "required_apis" {
  for_each = toset([
    "compute.googleapis.com",
    "container.googleapis.com",
    "run.googleapis.com",
    "aiplatform.googleapis.com",
    "secretmanager.googleapis.com",
    "cloudresourcemanager.googleapis.com",
    "monitoring.googleapis.com",
    "logging.googleapis.com",
  ])

  service            = each.value
  disable_on_destroy = false
}

# VPC Network
resource "google_compute_network" "vpc" {
  name                    = "${var.project_name}-vpc"
  auto_create_subnetworks = false
  depends_on              = [google_project_service.required_apis]
}

resource "google_compute_subnetwork" "subnet" {
  name          = "${var.project_name}-subnet"
  ip_cidr_range = "10.0.0.0/24"
  region        = var.region
  network       = google_compute_network.vpc.id

  secondary_ip_range {
    range_name    = "pods"
    ip_cidr_range = "10.1.0.0/16"
  }

  secondary_ip_range {
    range_name    = "services"
    ip_cidr_range = "10.2.0.0/16"
  }
}

# GKE Cluster (for Kafka and stateful services)
resource "google_container_cluster" "primary" {
  name     = "${var.project_name}-gke"
  location = var.region

  # Use autopilot for cost savings
  enable_autopilot = var.use_autopilot

  # Standard mode settings (if not autopilot)
  dynamic "node_pool" {
    for_each = var.use_autopilot ? [] : [1]
    content {
      name       = "default-pool"
      node_count = var.min_nodes

      node_config {
        machine_type = var.machine_type
        disk_size_gb = 20
        disk_type    = "pd-standard"

        # Use preemptible for cost savings
        preemptible  = var.use_preemptible

        oauth_scopes = [
          "https://www.googleapis.com/auth/cloud-platform"
        ]

        labels = {
          environment = var.environment
        }
      }

      autoscaling {
        min_node_count = var.min_nodes
        max_node_count = var.max_nodes
      }
    }
  }

  network    = google_compute_network.vpc.name
  subnetwork = google_compute_subnetwork.subnet.name

  ip_allocation_policy {
    cluster_secondary_range_name  = "pods"
    services_secondary_range_name = "services"
  }

  workload_identity_config {
    workload_pool = "${var.project_id}.svc.id.goog"
  }

  depends_on = [google_project_service.required_apis]
}

# Cloud Run for AI Gateway (serverless)
resource "google_cloud_run_v2_service" "ai_gateway" {
  name     = "ai-gateway"
  location = var.region

  template {
    containers {
      image = var.ai_gateway_image

      ports {
        container_port = 8002
      }

      env {
        name  = "REDIS_URL"
        value = "redis://${google_redis_instance.cache.host}:${google_redis_instance.cache.port}"
      }

      env {
        name = "GEMINI_API_KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.gemini_key.secret_id
            version = "latest"
          }
        }
      }

      env {
        name = "OPENAI_API_KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.openai_key.secret_id
            version = "latest"
          }
        }
      }

      env {
        name = "ANTHROPIC_API_KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.anthropic_key.secret_id
            version = "latest"
          }
        }
      }

      resources {
        limits = {
          cpu    = "1"
          memory = "512Mi"
        }
      }
    }

    scaling {
      min_instance_count = 0  # Scale to zero for cost savings
      max_instance_count = var.max_cloud_run_instances
    }
  }

  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }

  depends_on = [
    google_project_service.required_apis,
    google_secret_manager_secret_version.gemini_key,
    google_secret_manager_secret_version.openai_key,
    google_secret_manager_secret_version.anthropic_key
  ]
}

# Allow unauthenticated access to AI Gateway (or configure IAM)
resource "google_cloud_run_v2_service_iam_member" "ai_gateway_public" {
  count = var.allow_unauthenticated ? 1 : 0

  location = google_cloud_run_v2_service.ai_gateway.location
  name     = google_cloud_run_v2_service.ai_gateway.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# Redis Instance (for caching)
resource "google_redis_instance" "cache" {
  name           = "${var.project_name}-redis"
  tier           = var.redis_tier
  memory_size_gb = var.redis_memory_gb
  region         = var.region

  authorized_network = google_compute_network.vpc.id

  redis_version = "REDIS_7_0"
  display_name  = "AI Platform Cache"

  depends_on = [google_project_service.required_apis]
}

# Secret Manager for API Keys
resource "google_secret_manager_secret" "gemini_key" {
  secret_id = "gemini-api-key"

  replication {
    auto {}
  }

  depends_on = [google_project_service.required_apis]
}

resource "google_secret_manager_secret_version" "gemini_key" {
  secret      = google_secret_manager_secret.gemini_key.id
  secret_data = var.gemini_api_key != "" ? var.gemini_api_key : "placeholder"
}

resource "google_secret_manager_secret" "openai_key" {
  secret_id = "openai-api-key"

  replication {
    auto {}
  }

  depends_on = [google_project_service.required_apis]
}

resource "google_secret_manager_secret_version" "openai_key" {
  secret      = google_secret_manager_secret.openai_key.id
  secret_data = var.openai_api_key != "" ? var.openai_api_key : "placeholder"
}

resource "google_secret_manager_secret" "anthropic_key" {
  secret_id = "anthropic-api-key"

  replication {
    auto {}
  }

  depends_on = [google_project_service.required_apis]
}

resource "google_secret_manager_secret_version" "anthropic_key" {
  secret      = google_secret_manager_secret.anthropic_key.id
  secret_data = var.anthropic_api_key != "" ? var.anthropic_api_key : "placeholder"
}

# Cloud Storage for models/embeddings
resource "google_storage_bucket" "models" {
  name          = "${var.project_id}-ai-models"
  location      = var.region
  force_destroy = true

  uniform_bucket_level_access = true

  depends_on = [google_project_service.required_apis]
}

# Cloud Monitoring Dashboard
resource "google_monitoring_dashboard" "ai_platform" {
  dashboard_json = jsonencode({
    displayName = "AI Platform Dashboard"
    mosaicLayout = {
      columns = 12
      tiles = [
        {
          width  = 6
          height = 4
          widget = {
            title = "AI Gateway Request Rate"
            xyChart = {
              dataSets = [{
                timeSeriesQuery = {
                  timeSeriesFilter = {
                    filter = "resource.type=\"cloud_run_revision\" AND resource.labels.service_name=\"ai-gateway\""
                  }
                }
              }]
            }
          }
        },
        {
          width  = 6
          height = 4
          widget = {
            title = "AI Gateway Latency"
            xyChart = {
              dataSets = [{
                timeSeriesQuery = {
                  timeSeriesFilter = {
                    filter = "resource.type=\"cloud_run_revision\" AND resource.labels.service_name=\"ai-gateway\""
                  }
                }
              }]
            }
          }
        }
      ]
    }
  })

  depends_on = [google_project_service.required_apis]
}
