#!/bin/bash
# Register Avro schemas to Confluent Cloud Schema Registry
# Usage: ./scripts/register-schemas-confluent.sh

set -e

# Get credentials from environment or GCP secrets
SCHEMA_REGISTRY_URL="${SCHEMA_REGISTRY_URL:-$(gcloud secrets versions access latest --secret=confluent-schema-registry-url 2>/dev/null)}"
SR_API_KEY="${SR_API_KEY:-$(gcloud secrets versions access latest --secret=confluent-sr-api-key 2>/dev/null)}"
SR_API_SECRET="${SR_API_SECRET:-$(gcloud secrets versions access latest --secret=confluent-sr-api-secret 2>/dev/null)}"

if [ -z "$SCHEMA_REGISTRY_URL" ] || [ -z "$SR_API_KEY" ] || [ -z "$SR_API_SECRET" ]; then
    echo "❌ Missing Schema Registry credentials"
    echo "   Set SCHEMA_REGISTRY_URL, SR_API_KEY, SR_API_SECRET or configure GCP secrets"
    exit 1
fi

SCHEMAS_DIR="${1:-templates/supply-chain/schemas}"

echo "📋 Registering schemas to Confluent Cloud Schema Registry"
echo "   URL: $SCHEMA_REGISTRY_URL"
echo "   Schemas: $SCHEMAS_DIR"
echo ""

# Test connection
if ! curl -s -u "$SR_API_KEY:$SR_API_SECRET" "$SCHEMA_REGISTRY_URL/subjects" > /dev/null; then
    echo "❌ Cannot connect to Schema Registry"
    exit 1
fi

# Register each schema
for schema_file in "$SCHEMAS_DIR"/*.avsc; do
    if [ -f "$schema_file" ]; then
        schema_name=$(basename "$schema_file" .avsc)
        subject="${schema_name}-value"
        
        echo "📄 Registering: $subject"
        
        http_code=$(curl -s -o /tmp/sr_response.txt -w "%{http_code}" -X POST \
            -u "$SR_API_KEY:$SR_API_SECRET" \
            -H "Content-Type: application/vnd.schemaregistry.v1+json" \
            "$SCHEMA_REGISTRY_URL/subjects/${subject}/versions" \
            -d "{\"schemaType\": \"AVRO\", \"schema\": $(cat "$schema_file" | jq -Rs .)}")
        
        body=$(cat /tmp/sr_response.txt)
        
        if [ "$http_code" = "200" ]; then
            schema_id=$(echo "$body" | jq -r '.id')
            echo "   ✅ Registered (ID: $schema_id)"
        elif [ "$http_code" = "409" ]; then
            echo "   ⏭️  Already exists"
        else
            echo "   ❌ Failed (HTTP $http_code): $body"
        fi
    fi
done

# Also register with topic-specific subjects
echo ""
echo "📋 Registering topic-specific subjects..."

# Register order-events-value from order-event.avsc
if [ -f "$SCHEMAS_DIR/order-event.avsc" ]; then
    echo "📄 Registering: order-events-value (from order-event.avsc)"
    http_code=$(curl -s -o /tmp/sr_response.txt -w "%{http_code}" -X POST \
        -u "$SR_API_KEY:$SR_API_SECRET" \
        -H "Content-Type: application/vnd.schemaregistry.v1+json" \
        "$SCHEMA_REGISTRY_URL/subjects/order-events-value/versions" \
        -d "{\"schemaType\": \"AVRO\", \"schema\": $(cat "$SCHEMAS_DIR/order-event.avsc" | jq -Rs .)}")
    if [ "$http_code" = "200" ] || [ "$http_code" = "409" ]; then
        echo "   ✅ Done"
    else
        echo "   ❌ Failed (HTTP $http_code)"
    fi
fi

# Register supplier-events-value from supplier-event.avsc
if [ -f "$SCHEMAS_DIR/supplier-event.avsc" ]; then
    echo "📄 Registering: supplier-events-value (from supplier-event.avsc)"
    http_code=$(curl -s -o /tmp/sr_response.txt -w "%{http_code}" -X POST \
        -u "$SR_API_KEY:$SR_API_SECRET" \
        -H "Content-Type: application/vnd.schemaregistry.v1+json" \
        "$SCHEMA_REGISTRY_URL/subjects/supplier-events-value/versions" \
        -d "{\"schemaType\": \"AVRO\", \"schema\": $(cat "$SCHEMAS_DIR/supplier-event.avsc" | jq -Rs .)}")
    if [ "$http_code" = "200" ] || [ "$http_code" = "409" ]; then
        echo "   ✅ Done"
    else
        echo "   ❌ Failed (HTTP $http_code)"
    fi
fi

# Register product-events-value from product-created.avsc
if [ -f "$SCHEMAS_DIR/product-created.avsc" ]; then
    echo "📄 Registering: product-events-value (from product-created.avsc)"
    http_code=$(curl -s -o /tmp/sr_response.txt -w "%{http_code}" -X POST \
        -u "$SR_API_KEY:$SR_API_SECRET" \
        -H "Content-Type: application/vnd.schemaregistry.v1+json" \
        "$SCHEMA_REGISTRY_URL/subjects/product-events-value/versions" \
        -d "{\"schemaType\": \"AVRO\", \"schema\": $(cat "$SCHEMAS_DIR/product-created.avsc" | jq -Rs .)}")
    if [ "$http_code" = "200" ] || [ "$http_code" = "409" ]; then
        echo "   ✅ Done"
    else
        echo "   ❌ Failed (HTTP $http_code)"
    fi
fi

# Cleanup
rm -f /tmp/sr_response.txt

echo ""
echo "✅ Schema registration complete"
echo ""
echo "Registered subjects:"
curl -s -u "$SR_API_KEY:$SR_API_SECRET" "$SCHEMA_REGISTRY_URL/subjects" | jq -r '.[]' | sed 's/^/   /'
