#!/bin/bash

# === Configuration ===
BILLING_ACCOUNT_ID="YOUR-BILLING-ACCOUNT-ID"  # Replace with yours
PROJECT_NAME="platform-dev-$(date +%Y%m%d)"
REGION="us-central1"

echo "🚀 Creating new GCP project for Platform Development"
echo "=================================================="

# 1. Create project
echo "📝 Creating project: $PROJECT_NAME"
gcloud projects create $PROJECT_NAME --name="Intelligent Platform Dev"

# 2. Set as active project
echo "🎯 Setting active project"
gcloud config set project $PROJECT_NAME

# 3. Link billing
echo "💳 Linking billing account"
gcloud billing projects link $PROJECT_NAME \
  --billing-account=$BILLING_ACCOUNT_ID

# 4. Enable required APIs
echo "🔧 Enabling required APIs (this takes a minute)..."
gcloud services enable \
  container.googleapis.com \
  compute.googleapis.com \
  aiplatform.googleapis.com \
  storage-api.googleapis.com \
  secretmanager.googleapis.com \
  artifactregistry.googleapis.com

# 5. Create service account
echo "🔐 Creating service account"
gcloud iam service-accounts create platform-dev-sa \
  --display-name="Platform Dev Service Account"

# 6. Grant permissions
echo "🔑 Granting permissions"
gcloud projects add-iam-policy-binding $PROJECT_NAME \
  --member="serviceAccount:platform-dev-sa@${PROJECT_NAME}.iam.gserviceaccount.com" \
  --role="roles/owner" \
  --quiet

# 7. Download credentials
echo "📥 Downloading credentials"
mkdir -p ~/.config/gcloud
gcloud iam service-accounts keys create \
  ~/.config/gcloud/platform-dev-sa.json \
  --iam-account=platform-dev-sa@${PROJECT_NAME}.iam.gserviceaccount.com

echo ""
echo "✅ Setup complete!"
echo "=================================================="
echo ""
echo "📝 Add to your .env file:"
echo ""
echo "GOOGLE_APPLICATION_CREDENTIALS=$HOME/.config/gcloud/platform-dev-sa.json"
echo "GCP_PROJECT_ID=$PROJECT_NAME"
echo "GCP_REGION=$REGION"
echo ""
echo "🎯 Project URL:"
echo "https://console.cloud.google.com/home/dashboard?project=$PROJECT_NAME"