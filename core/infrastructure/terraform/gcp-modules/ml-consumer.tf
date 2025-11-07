# terraform/ml-consumer.tf
# ML Consumer - Processes Kafka events and trains models

# ==============================================================================
# ML CONSUMER CONFIGMAP
# ==============================================================================

resource "kubernetes_config_map" "ml_consumer" {
  metadata {
    name      = "ml-consumer-config"
    namespace = "default"
  }

  data = {
    KAFKA_BOOTSTRAP_SERVERS = "kafka:9092"
    KAFKA_CONSUMER_GROUP    = "ml-consumer-group"
    KAFKA_TOPICS            = "supply-chain.orders,supply-chain.predictions"
    MLFLOW_TRACKING_URI     = "http://mlflow:5000"
    METRICS_PORT            = "9090"
    LOG_LEVEL               = "INFO"

    # Model training settings
    TRAINING_BATCH_SIZE     = "100"
    TRAINING_INTERVAL_SEC   = "300"  # Train every 5 minutes
    MODEL_NAME              = "supply-chain-classifier"

    # Feature engineering
    ENABLE_FEATURE_ENGINEERING = "true"

    # Performance settings
    MAX_POLL_RECORDS        = "500"
    SESSION_TIMEOUT_MS      = "30000"
    MAX_POLL_INTERVAL_MS    = "300000"
  }

  depends_on = [google_container_cluster.primary]
}

# ==============================================================================
# ML CONSUMER DEPLOYMENT
# ==============================================================================

resource "kubernetes_deployment" "ml_consumer" {
  metadata {
    name      = "ml-consumer"
    namespace = "default"
    labels = {
      app = "ml-consumer"
    }
  }

  spec {
    replicas = 1

    selector {
      match_labels = {
        app = "ml-consumer"
      }
    }

    template {
      metadata {
        labels = {
          app = "ml-consumer"
        }
        annotations = {
          "prometheus.io/scrape" = "true"
          "prometheus.io/port"   = "9090"
          "prometheus.io/path"   = "/metrics"
        }
      }

      spec {
        # Init container to wait for Kafka
        init_container {
          name  = "wait-for-kafka"
          image = "busybox:latest"

          command = [
            "sh",
            "-c",
            "until nc -z kafka 9092; do echo waiting for kafka; sleep 2; done"
          ]
        }

        # Init container to wait for MLflow
        init_container {
          name  = "wait-for-mlflow"
          image = "curlimages/curl:latest"

          command = [
            "sh",
            "-c",
            "until curl -f http://mlflow:5000/health 2>/dev/null; do echo waiting for mlflow; sleep 5; done"
          ]
        }

        container {
          name  = "ml-consumer"
          image = "${var.region}-docker.pkg.dev/${var.project_id}/ai-platform/ml-consumer:latest"

          port {
            container_port = 9090
            name           = "metrics"
            protocol       = "TCP"
          }

          env_from {
            config_map_ref {
              name = kubernetes_config_map.ml_consumer.metadata[0].name
            }
          }

          # Additional environment variables
          env {
            name  = "GCP_PROJECT_ID"
            value = var.project_id
          }

          env {
            name  = "GCP_REGION"
            value = var.region
          }

          env {
            name  = "MODELS_BUCKET"
            value = google_storage_bucket.models.name
          }

          # Python settings
          env {
            name  = "PYTHONUNBUFFERED"
            value = "1"
          }

          resources {
            requests = {
              cpu    = "500m"
              memory = "1Gi"
            }
            limits = {
              cpu    = "2000m"
              memory = "4Gi"
            }
          }

          # Liveness probe - check if consumer is running
          liveness_probe {
            http_get {
              path = "/metrics"
              port = 9090
            }
            initial_delay_seconds = 60
            period_seconds        = 30
            timeout_seconds       = 10
            failure_threshold     = 5
          }

          # Readiness probe - check if ready to process
          readiness_probe {
            http_get {
              path = "/metrics"
              port = 9090
            }
            initial_delay_seconds = 30
            period_seconds        = 10
            timeout_seconds       = 5
            failure_threshold     = 3
          }

          # Lifecycle hooks
          lifecycle {
            pre_stop {
              exec {
                command = ["/bin/sh", "-c", "sleep 10"]
              }
            }
          }
        }

        # Service account for GCS access
        service_account_name = "default"

        # Tolerate Autopilot node constraints
        dynamic "toleration" {
          for_each = var.use_autopilot ? [1] : []
          content {
            effect = "NoSchedule"
            key    = "cloud.google.com/gke-preemptible"
          }
        }

        # Restart policy
        restart_policy = "Always"
      }
    }

    strategy {
      type = "RollingUpdate"

      rolling_update {
        max_unavailable = 0
        max_surge       = 1
      }
    }
  }

  depends_on = [
    kubernetes_config_map.ml_consumer
  ]

  # Ignore image changes if deploying manually
  lifecycle {
    ignore_changes = [
      metadata[0].annotations,
      spec[0].template[0].metadata[0].annotations,
      spec[0].template[0].spec[0].container[0].image,
      spec[0].template[0].spec[0].container[0].resources,
      spec[0].template[0].spec[0].init_container[0].resources,
    ]
  }
}

# ==============================================================================
# ML CONSUMER SERVICE (for metrics)
# ==============================================================================

resource "kubernetes_service" "ml_consumer" {
  metadata {
    name      = "ml-consumer"
    namespace = "default"
    labels = {
      app = "ml-consumer"
    }
  }

  spec {
    type = "LoadBalancer"

    selector = {
      app = "ml-consumer"
    }

    port {
      name        = "metrics"
      port        = 9090
      target_port = 9090
      protocol    = "TCP"
    }
  }

  depends_on = [google_container_cluster.primary]
}

# # ==============================================================================
# # HORIZONTAL POD AUTOSCALER (optional)
# # ==============================================================================

# resource "kubernetes_horizontal_pod_autoscaler_v2" "ml_consumer" {
#   metadata {
#     name      = "ml-consumer"
#     namespace = "default"
#   }

#   spec {
#     scale_target_ref {
#       api_version = "apps/v1"
#       kind        = "Deployment"
#       name        = kubernetes_deployment.ml_consumer.metadata[0].name
#     }

#     min_replicas = 1
#     max_replicas = 3

#     metric {
#       type = "Resource"
#       resource {
#         name = "cpu"
#         target {
#           type                = "Utilization"
#           average_utilization = 80
#         }
#       }
#     }

#     metric {
#       type = "Resource"
#       resource {
#         name = "memory"
#         target {
#           type                = "Utilization"
#           average_utilization = 80
#         }
#       }
#     }

#     behavior {
#       scale_down {
#         stabilization_window_seconds = 300
#         policy {
#           type           = "Percent"
#           value          = 50
#           period_seconds = 60
#         }
#       }

#       scale_up {
#         stabilization_window_seconds = 0
#         policy {
#           type           = "Percent"
#           value          = 100
#           period_seconds = 30
#         }
#       }
#     }
#   }

#   depends_on = [kubernetes_deployment.ml_consumer]
# }

# ==============================================================================
# OUTPUTS
# ==============================================================================

output "ml_consumer_metrics_url" {
  value       = "http://${kubernetes_service.ml_consumer.metadata[0].name}:9090/metrics"
  description = "ML Consumer metrics endpoint URL"
}

output "ml_consumer_service_ip" {
  value       = kubernetes_service.ml_consumer.spec[0].cluster_ip
  description = "ML Consumer ClusterIP for internal access"
}
