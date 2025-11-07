# Read existing secret from Secret Manager
data "google_secret_manager_secret_version" "pinecone_api_key" {
  secret  = "pinecone-api-key"
  project = var.project_id
}

# Create Kubernetes secret
resource "kubernetes_secret" "pinecone" {
  metadata {
    name = "pinecone-secret"
  }

  data = {
    api-key = data.google_secret_manager_secret_version.pinecone_api_key.secret_data
  }

  type = "Opaque"
  
  depends_on = [google_container_cluster.primary]
}