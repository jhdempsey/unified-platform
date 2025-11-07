#!/bin/bash
# Automated Kafka topic creation using docker exec

set -e

KAFKA_CONTAINER="platform-kafka"
BOOTSTRAP_SERVER="localhost:9092"

echo "📋 Creating Kafka topics..."

# Define topics
declare -A TOPICS=(
    ["order-events"]=3
    ["supplier-events"]=3
    ["product-created"]=3
    ["quality-alerts"]=3
    ["lineage-events"]=3
)

# Create each topic
for topic in "${!TOPICS[@]}"; do
    partitions=${TOPICS[$topic]}
    echo "  → Creating topic: $topic (partitions: $partitions)"
    
    docker exec $KAFKA_CONTAINER kafka-topics \
        --bootstrap-server $BOOTSTRAP_SERVER \
        --create \
        --topic $topic \
        --partitions $partitions \
        --replication-factor 1 \
        --if-not-exists 2>/dev/null || true
done

echo ""
echo "✅ Kafka topics created"
echo ""
echo "📊 Current topics:"
docker exec $KAFKA_CONTAINER kafka-topics --bootstrap-server $BOOTSTRAP_SERVER --list | grep -v "^_"
