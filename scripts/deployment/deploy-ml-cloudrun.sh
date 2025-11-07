#!/bin/bash
# Deploy Model Inference Service to Cloud Run
# Matches your existing services (Dashboard, RAG, AI Gateway)

set -e

PROJECT_ID=${GOOGLE_CLOUD_PROJECT:-$(gcloud config get-value project)}
REGION=${REGION:-"us-central1"}
SERVICE_NAME="model-inference"
IMAGE_NAME="$REGION-docker.pkg.dev/$PROJECT_ID/ai-platform/$SERVICE_NAME:latest"

# Get MLflow URL (from GKE)
MLFLOW_IP=$(kubectl get svc mlflow -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "")
if [ -z "$MLFLOW_IP" ]; then
    echo "⚠️  Warning: Could not get MLflow IP. Service may not track experiments."
    MLFLOW_URL="http://mlflow.default.svc.cluster.local:5000"
else
    MLFLOW_URL="http://$MLFLOW_IP:5000"
fi

echo "╔════════════════════════════════════════════════════════════╗"
echo "║      Deploy Model Inference Service to Cloud Run          ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "Project:      $PROJECT_ID"
echo "Region:       $REGION"
echo "Service:      $SERVICE_NAME"
echo "MLflow URL:   $MLFLOW_URL"
echo ""

# Step 1: Build image using Cloud Build (most reliable)
echo "════════════════════════════════════════════════════════════"
echo "Step 1/2: Building Image via Cloud Build"
echo "════════════════════════════════════════════════════════════"
echo ""

# Create temporary cloudbuild.yaml
cat > /tmp/cloudbuild-model-inference.yaml << EOF
steps:
  - name: 'gcr.io/cloud-builders/docker'
    args:
      - 'build'
      - '-f'
      - 'services/model-inference/Dockerfile'
      - '-t'
      - '$IMAGE_NAME'
      - '.'
images:
  - '$IMAGE_NAME'
timeout: 1200s
EOF

gcloud builds submit \
  --config=/tmp/cloudbuild-model-inference.yaml \
  --project=$PROJECT_ID \
  .

if [ $? -eq 0 ]; then
    echo "✅ Image built and pushed successfully"
    rm /tmp/cloudbuild-model-inference.yaml
else
    echo "❌ Build failed"
    rm /tmp/cloudbuild-model-inference.yaml
    exit 1
fi
echo ""

# Step 2: Deploy to Cloud Run
echo "════════════════════════════════════════════════════════════"
echo "Step 2/2: Deploying to Cloud Run"
echo "════════════════════════════════════════════════════════════"
echo ""

gcloud run deploy $SERVICE_NAME \
  --image $IMAGE_NAME \
  --platform managed \
  --region $REGION \
  --project $PROJECT_ID \
  --allow-unauthenticated \
  --port 8001 \
  --memory 2Gi \
  --cpu 2 \
  --timeout 300 \
  --concurrency 80 \
  --min-instances 0 \
  --max-instances 10 \
  --set-env-vars="MLFLOW_TRACKING_URI=$MLFLOW_URL,PYTHONUNBUFFERED=1"

if [ $? -eq 0 ]; then
    echo "✅ Service deployed successfully"
else
    echo "❌ Deployment failed"
    exit 1
fi
echo ""

# Get service URL
echo "════════════════════════════════════════════════════════════"
echo "🎉 Deployment Complete!"
echo "════════════════════════════════════════════════════════════"
echo ""

SERVICE_URL=$(gcloud run services describe $SERVICE_NAME \
  --platform managed \
  --region $REGION \
  --format 'value(status.url)')

echo "✅ Service URL: $SERVICE_URL"
echo ""
echo "📋 Update Dashboard:"
echo "────────────────────────────────────────────────────────────"
echo "MODEL_INFERENCE_URL = \"$SERVICE_URL\""
echo ""
echo "🧪 Test Endpoints:"
echo "────────────────────────────────────────────────────────────"
echo "Health:   curl $SERVICE_URL/health"
echo "Models:   curl $SERVICE_URL/models"
echo "Predict:  curl -X POST $SERVICE_URL/predict/demand \\"
echo "            -H 'Content-Type: application/json' \\"
echo "            -d '{...}'"
echo ""
echo "📊 View Logs:"
echo "────────────────────────────────────────────────────────────"
echo "gcloud run services logs read $SERVICE_NAME --region $REGION"
echo ""
echo "🌐 Other Services:"
echo "────────────────────────────────────────────────────────────"
echo "Dashboard:   https://dashboard-dakmfhg3aa-uc.a.run.app"
echo "RAG Service: https://rag-service-742330383495.us-central1.run.app"
echo "AI Gateway:  https://ai-gateway-dakmfhg3aa-uc.a.run.app"
echo "MLflow:      $MLFLOW_URL"
echo ""
echo "💡 Note: First request may take 60-90s (cold start + model training)"
echo ""
