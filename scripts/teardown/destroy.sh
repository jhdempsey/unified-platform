#!/bin/bash
# Destroy GCP Infrastructure

set -e

echo "🧹 AI Platform - Destroy GCP Resources"
echo "======================================"
echo ""
echo "⚠️  WARNING: This will destroy all GCP resources!"
echo ""
read -p "Are you sure? Type 'destroy' to confirm: " confirm

if [ "$confirm" != "destroy" ]; then
    echo "❌ Cancelled"
    exit 0
fi

cd terraform

echo ""
echo "🗑️  Destroying infrastructure..."
terraform destroy -auto-approve

echo ""
echo "✅ All resources destroyed"
echo ""
echo "💰 Cost stopped!"

cd ..
