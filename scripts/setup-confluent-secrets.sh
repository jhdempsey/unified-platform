#!/bin/bash
# Setup GCP Secret Manager secrets for Confluent Cloud
# Usage: ./scripts/setup-confluent-secrets.sh
#
# This script creates or updates secrets without trailing newlines

set -e

PROJECT_ID="${GCP_PROJECT_ID:-gen-lang-client-0282248851}"

echo "🔐 Setting up Confluent Cloud secrets in GCP Secret Manager"
echo "   Project: $PROJECT_ID"
echo ""

# Function to create or update a secret
create_or_update_secret() {
    local secret_name=$1
    local prompt=$2
    local current_value=""
    
    # Check if secret exists
    if gcloud secrets describe "$secret_name" --project="$PROJECT_ID" &>/dev/null; then
        current_value=$(gcloud secrets versions access latest --secret="$secret_name" --project="$PROJECT_ID" 2>/dev/null || true)
        echo "📝 $secret_name exists (current length: ${#current_value})"
    else
        echo "📝 $secret_name does not exist, creating..."
        gcloud secrets create "$secret_name" --project="$PROJECT_ID" --replication-policy="automatic"
    fi
    
    # Prompt for value
    echo "   $prompt"
    echo -n "   Enter value (or press Enter to skip): "
    read -r value
    
    if [ -n "$value" ]; then
        # Add new version without trailing newline
        echo -n "$value" | gcloud secrets versions add "$secret_name" --project="$PROJECT_ID" --data-file=-
        echo "   ✅ Updated"
    else
        echo "   ⏭️  Skipped"
    fi
    echo ""
}

echo "=== Kafka Cluster Credentials ==="
create_or_update_secret "confluent-bootstrap-server" "Kafka bootstrap server (e.g., pkc-xxxxx.region.azure.confluent.cloud:9092)"
create_or_update_secret "confluent-kafka-api-key" "Kafka API Key"
create_or_update_secret "confluent-kafka-api-secret" "Kafka API Secret"

echo "=== Schema Registry Credentials ==="
create_or_update_secret "confluent-schema-registry-url" "Schema Registry URL (e.g., https://psrc-xxxxx.region.azure.confluent.cloud)"
create_or_update_secret "confluent-sr-api-key" "Schema Registry API Key"
create_or_update_secret "confluent-sr-api-secret" "Schema Registry API Secret"

echo ""
echo "✅ Secret setup complete"
echo ""
echo "=== Verify secrets ==="
for secret in confluent-bootstrap-server confluent-kafka-api-key confluent-schema-registry-url confluent-sr-api-key; do
    val=$(gcloud secrets versions access latest --secret="$secret" --project="$PROJECT_ID" 2>/dev/null || echo "NOT SET")
    if [ "$val" != "NOT SET" ]; then
        # Mask the value
        masked="${val:0:10}..."
        echo "   $secret: $masked (length: ${#val})"
    else
        echo "   $secret: NOT SET"
    fi
done

echo ""
echo "=== Next Steps ==="
echo "1. Run Terraform to deploy services with these secrets:"
echo "   cd core/infrastructure/terraform/gcp-modules && terraform apply"
echo ""
echo "2. Register schemas:"
echo "   ./scripts/register-schemas-confluent.sh"
