#!/bin/bash
set -e

ENVIRONMENT=${1:-dev}
VERTICAL=${2:-supply-chain}

echo "🚀 Bootstrapping Platform"
echo "   Environment: $ENVIRONMENT"
echo "   Vertical: $VERTICAL"
echo ""

# Source .env file if it exists - export all non-comment lines
if [ -f .env ]; then
    set -a  # automatically export all variables
    source .env
    set +a
    echo "✅ Loaded environment variables from .env"
    echo ""
fi

# Wait for services
echo "⏳ Waiting for services to be healthy..."
sleep 30

# 1. Create Kafka topics (bash-based, automated)
echo "1️⃣ Creating Kafka topics..."
bash scripts/bootstrap/create-kafka-topics.sh

# 2. Register schemas
echo ""
echo "2️⃣ Registering Avro schemas..."
bash scripts/bootstrap/register-schemas.sh "$VERTICAL"

# 3. Setup Pinecone (with proper env var passing)
echo ""
echo "3️⃣ Setting up Pinecone..."
export PINECONE_API_KEY="${PINECONE_API_KEY}"
export PINECONE_ENVIRONMENT="${PINECONE_ENVIRONMENT}"
bash scripts/bootstrap/setup-pinecone.sh "$ENVIRONMENT"

# 4. Initialize MLflow
echo ""
echo "4️⃣ Initializing MLflow..."
bash scripts/bootstrap/init-mlflow.sh "$VERTICAL"

echo ""
echo "✅ Bootstrap complete!"
echo "   Platform ready for vertical: $VERTICAL"
