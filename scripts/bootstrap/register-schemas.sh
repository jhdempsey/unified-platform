#!/bin/bash
# Register Avro schemas to Schema Registry

# Use environment variable or default to localhost for local dev
SCHEMA_REGISTRY_URL="${SCHEMA_REGISTRY_URL:-http://localhost:8081}"
VERTICAL="${1:-supply-chain}"
SCHEMAS_DIR="templates/${VERTICAL}/schemas"

echo "📄 Registering schemas for vertical: $VERTICAL"
echo "   Schema Registry: $SCHEMA_REGISTRY_URL"

if [ ! -d "$SCHEMAS_DIR" ]; then
    echo "❌ Schemas directory not found: $SCHEMAS_DIR"
    exit 1
fi

for schema_file in "$SCHEMAS_DIR"/*.avsc; do
    if [ -f "$schema_file" ]; then
        schema_name=$(basename "$schema_file" .avsc)
        echo "  → Registering $schema_name"
        
        response=$(curl -s -w "\n%{http_code}" -X POST "$SCHEMA_REGISTRY_URL/subjects/${schema_name}-value/versions" \
             -H "Content-Type: application/vnd.schemaregistry.v1+json" \
             -d "{\"schema\": $(cat "$schema_file" | jq -Rs .)}")
        
        http_code=$(echo "$response" | tail -1)
        
        if [ "$http_code" = "200" ] || [ "$http_code" = "409" ]; then
            echo "    ✓ Registered"
        else
            echo "    ✗ Failed (HTTP $http_code)"
        fi
    fi
done

echo "✅ Schema registration complete"
