# Firewall rule to allow GKE pods to reach Cloud SQL on default network
resource "google_compute_firewall" "allow_gke_to_cloudsql" {
  name    = "allow-gke-to-cloudsql"
  network = "default"

  allow {
    protocol = "tcp"
    ports    = ["5432"]  # PostgreSQL
  }

  # Allow from GKE subnets
  source_ranges = [
    "10.0.0.0/24",   # ai-platform-subnet
    "10.1.0.0/16",   # pods
    "10.2.0.0/16"    # services
  ]

  description = "Allow GKE pods from ai-platform-vpc to reach Cloud SQL on default network"
}
