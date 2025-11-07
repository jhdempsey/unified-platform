#!/bin/bash
# GCP Deployment Script for AI Platform

set -e

echo "🚀 AI Platform - GCP Deployment"
echo "================================"

# Configuration
PROJECT_ID=${GCP_PROJECT_ID:-"your-project-id"}
REGION=${GCP_REGION:-"us-central1"}
IMAGE_TAG=${IMAGE_TAG:-"latest"}

echo ""
echo "📋 Configuration:"
echo "   Project ID: $PROJECT_ID"
echo "   Region: $REGION"
echo "   Image Tag: $IMAGE_TAG"
echo ""

# Check prerequisites
echo "🔍 Checking prerequisites..."

if ! command -v gcloud &> /dev/null; then
    echo "❌ gcloud CLI not found. Install from: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

if ! command -v terraform &> /dev/null; then
    echo "❌ terraform not found. Install from: https://www.terraform.io/downloads"
    exit 1
fi

if ! command -v kubectl &> /dev/null; then
    echo "❌ kubectl not found. Install from: https://kubernetes.io/docs/tasks/tools/"
    exit 1
fi

echo "✅ Prerequisites OK"

# Authenticate and set project
echo ""
echo "🔐 Authenticating with GCP..."
gcloud config set project $PROJECT_ID
gcloud auth application-default login

# Build and push Docker images
echo ""
echo "🐳 Building Docker images..."

# Enable Container Registry API
gcloud services enable containerregistry.googleapis.com

# Configure Docker for GCR
gcloud auth configure-docker

# Build AI Gateway
echo "Building AI Gateway..."
docker build --platform linux/amd64 -t gcr.io/$PROJECT_ID/ai-gateway:$IMAGE_TAG \
  -f services/ai-gateway/Dockerfile \
  services/ai-gateway/

docker push gcr.io/$PROJECT_ID/ai-gateway:$IMAGE_TAG

echo "✅ Images built and pushed"

# Initialize Terraform
echo ""
echo "📦 Initializing Terraform..."
cd terraform
terraform init

# Create terraform.tfvars if it doesn't exist
if [ ! -f terraform.tfvars ]; then
    echo "📝 Creating terraform.tfvars..."
    cat > terraform.tfvars <<EOF
project_id   = "$PROJECT_ID"
project_name = "ai-platform"
region       = "$REGION"
environment  = "demo"

use_autopilot    = true
use_preemptible  = true
redis_tier       = "BASIC"
redis_memory_gb  = 1
min_nodes        = 1
max_nodes        = 3

allow_unauthenticated = true

ai_gateway_image = "gcr.io/$PROJECT_ID/ai-gateway:$IMAGE_TAG"
EOF
fi

# Plan
echo ""
echo "📋 Planning Terraform changes..."
terraform plan -out=tfplan

# Apply
echo ""
read -p "Apply these changes? (yes/no): " confirm
if [ "$confirm" = "yes" ]; then
    echo "🚀 Applying Terraform..."
    terraform apply tfplan

    # Get outputs
    echo ""
    echo "📊 Deployment outputs:"
    terraform output

    # Configure kubectl
    echo ""
    echo "🔧 Configuring kubectl..."
    CLUSTER_NAME=$(terraform output -raw gke_cluster_name)
    gcloud container clusters get-credentials $CLUSTER_NAME \
      --region $REGION \
      --project $PROJECT_ID

    # Deploy Kafka to GKE
    echo ""
    echo "📦 Deploying Kafka to GKE..."
    kubectl apply -f ../k8s/kafka-statefulset.yaml

    # Wait for Kafka
    echo "⏳ Waiting for Kafka to be ready..."
    kubectl wait --for=condition=ready pod/kafka-0 --timeout=300s

    echo ""
    echo "✅ Deployment complete!"
    echo ""
    echo "🌐 AI Gateway URL:"
    terraform output ai_gateway_url
    echo ""
    echo "📊 Monitoring Dashboard:"
    echo "   https://console.cloud.google.com/monitoring/dashboards"
    echo ""
    echo "💰 Estimated monthly cost: ~$50-100 (with preemptible nodes)"
    echo ""
    echo "🧹 To tear down: ./destroy.sh"
else
    echo "❌ Deployment cancelled"
    rm tfplan
fi

cd ..
