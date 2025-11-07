#!/bin/bash
set -e

echo "🚀 Deploying AI Platform to GKE with Metrics API"
echo "=================================================="

PROJECT_ID=$(gcloud config get-value project)
REGION="us-central1"
ML_CONSUMER_IMAGE="us-central1-docker.pkg.dev/${PROJECT_ID}/ai-platform/ml-consumer:latest"

# Get current context
CONTEXT=$(kubectl config current-context)
echo "📍 Kubernetes Context: $CONTEXT"
echo "📍 Project ID: $PROJECT_ID"
echo ""

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

# Step 0: Build and push ML Consumer image
echo "📦 Step 0: Building ML Consumer image..."
echo "🖼️  Target image: $ML_CONSUMER_IMAGE"

# Check if we should build
if [ "${SKIP_BUILD:-false}" != "true" ]; then
    echo "🏗️  Building via Cloud Build (this may take 2-3 minutes)..."

    gcloud builds submit \
        --config=cloudbuild-ml-consumer.yaml \
        --substitutions=_IMAGE_NAME=${ML_CONSUMER_IMAGE} \
        --project ${PROJECT_ID} \
        --timeout=10m \
        .

    echo "✅ Image built and pushed"
else
    echo "⏭️  Skipping build (SKIP_BUILD=true)"
fi
echo ""

# Step 1: Deploy Kafka and Schema Registry
echo "📦 Step 1: Deploying Kafka and Schema Registry..."
kubectl apply -f k8s/kafka-statefulset.yaml

echo "⏳ Waiting for Kafka to be ready..."
kubectl wait --for=condition=ready pod -l app=kafka --timeout=300s

echo "⏳ Waiting for Schema Registry to be ready..."
kubectl wait --for=condition=ready pod -l app=schema-registry --timeout=300s

echo "✅ Kafka and Schema Registry are ready"
echo ""

# Step 2: Create Kafka Topics
echo "📦 Step 2: Creating Kafka topics..."
kubectl delete job kafka-topics-init --ignore-not-found=true
kubectl apply -f k8s/kafka-topics-job.yaml

echo "⏳ Waiting for topic creation to complete..."
kubectl wait --for=condition=complete job/kafka-topics-init --timeout=120s

echo "✅ Topics created"
echo ""

# Step 3: Deploy ML Consumer with Metrics API
echo "📦 Step 3: Deploying ML Consumer with Metrics API..."
echo "🖼️  Using image: $ML_CONSUMER_IMAGE"

kubectl apply -f k8s/ml-consumer-deployment.yaml
kubectl set image deployment/ml-consumer ml-consumer=${ML_CONSUMER_IMAGE}

echo "⏳ Waiting for ML Consumer to be ready..."
kubectl wait --for=condition=ready pod -l app=ml-consumer --timeout=180s

echo "✅ ML Consumer is ready"
echo ""

# Step 4: Wait for LoadBalancer IP
echo "📦 Step 4: Getting LoadBalancer external IP..."
echo "⏳ This may take 1-2 minutes..."

METRICS_IP=""
for i in {1..40}; do
    METRICS_IP=$(kubectl get svc ml-consumer -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "")

    if [ -n "$METRICS_IP" ]; then
        echo "✅ LoadBalancer ready"
        break
    fi

    if [ $((i % 5)) -eq 0 ]; then
        echo "   Still waiting... (attempt $i/40)"
    fi
    sleep 5
done

if [ -z "$METRICS_IP" ]; then
    echo "⚠️  LoadBalancer IP not ready yet"
    echo "   Check status with: kubectl get svc ml-consumer"
else
    # Save IP to file
    echo "${METRICS_IP}" > /tmp/ml-consumer-metrics-ip.txt

    # Test health endpoint
    echo ""
    echo "🧪 Testing Metrics API..."
    sleep 5  # Give service a moment to start

    if curl -f -s "http://${METRICS_IP}/health" > /dev/null 2>&1; then
        echo "✅ Metrics API is responding"
    else
        echo "⚠️  Metrics API not responding yet (may still be starting)"
    fi
fi

echo ""

# Summary
echo "=================================================="
echo "✅ Deployment Complete!"
echo "=================================================="
echo ""

echo "📊 Current Status:"
kubectl get pods,svc -l app=ml-consumer
echo ""

echo "📋 Kafka Topics:"
kubectl exec -it kafka-0 -- kafka-topics --list --bootstrap-server localhost:9092 2>/dev/null || echo "  (Run manually if needed)"
echo ""

if [ -n "$METRICS_IP" ]; then
    echo "=================================================="
    echo "📊 Metrics API Endpoints:"
    echo "=================================================="
    echo ""
    echo "  Base URL:       http://${METRICS_IP}"
    echo "  Health Check:   http://${METRICS_IP}/health"
    echo "  Kafka Metrics:  http://${METRICS_IP}/metrics/kafka"
    echo "  Consumer Stats: http://${METRICS_IP}/metrics/consumer"
    echo "  Prometheus:     http://${METRICS_IP}/metrics"
    echo "  API Docs:       http://${METRICS_IP}/docs"
    echo ""
    echo "📝 IP saved to: /tmp/ml-consumer-metrics-ip.txt"
    echo ""
    echo "🧪 Quick Test:"
    echo "  curl http://${METRICS_IP}/health | jq"
    echo "  curl http://${METRICS_IP}/metrics/kafka | jq"
    echo ""
fi

echo "=================================================="
echo "🎯 Next Steps:"
echo "=================================================="
echo ""
echo "1. Deploy event producers:"
echo "   kubectl apply -f k8s/event-producer-cronjob.yaml"
echo ""
echo "2. View ML Consumer logs:"
echo "   kubectl logs -l app=ml-consumer -f"
echo ""
echo "3. Update Dashboard with Metrics API URL:"
echo "   # Edit services/dashboard/streamlit_app.py"
echo "   METRICS_API_URL = \"http://${METRICS_IP:-YOUR_IP}\""
echo "   # Then redeploy:"
echo "   ./scripts/deploy_dashboard.sh"
echo ""
echo "4. Monitor metrics:"
echo "   watch -n 2 'curl -s http://${METRICS_IP:-YOUR_IP}/metrics/consumer | jq'"
echo ""

# Optional: Display help for troubleshooting
if [ -z "$METRICS_IP" ]; then
    echo "⚠️  Troubleshooting LoadBalancer:"
    echo "   kubectl describe svc ml-consumer"
    echo "   kubectl get events --sort-by='.lastTimestamp'"
    echo ""
fi
