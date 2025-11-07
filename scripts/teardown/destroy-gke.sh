#!/bin/bash
set -e

echo "🗑️  Destroying AI Platform from GKE"
echo "===================================="

# Delete in reverse order
echo "📦 Deleting ML Consumer..."
kubectl delete -f k8s/ml-consumer-deployment.yaml --ignore-not-found=true

echo "📦 Deleting Kafka topics job..."
kubectl delete job kafka-topics-init --ignore-not-found=true

echo "📦 Deleting Kafka and Schema Registry..."
kubectl delete -f k8s/kafka-statefulset.yaml --ignore-not-found=true

echo "⏳ Waiting for pods to terminate..."
kubectl wait --for=delete pod -l app=kafka --timeout=60s || true
kubectl wait --for=delete pod -l app=schema-registry --timeout=60s || true
kubectl wait --for=delete pod -l app=ml-consumer --timeout=60s || true

echo ""
echo "✅ Cleanup complete!"
echo ""
echo "📊 Remaining resources:"
kubectl get pods
