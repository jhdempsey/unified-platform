#!/bin/bash
# Setup Pinecone vector database per environment

ENVIRONMENT=${1:-dev}
INDEX_NAME="supply-chain-docs-${ENVIRONMENT}"
PINECONE_CLOUD="${PINECONE_CLOUD:-aws}"
PINECONE_REGION="${PINECONE_REGION:-us-east-1}"

# Check if API key is set
if [ -z "$PINECONE_API_KEY" ]; then
    echo "⚠️  PINECONE_API_KEY not set - skipping Pinecone setup"
    echo "   Set it in .env or export PINECONE_API_KEY=your-key"
    exit 0
fi

echo "🔮 Setting up Pinecone for environment: $ENVIRONMENT"
echo "   Index: $INDEX_NAME"
echo "   Cloud: $PINECONE_CLOUD"
echo "   Region: $PINECONE_REGION"

python3 << EOF
from pinecone import Pinecone, ServerlessSpec
import os
import sys

api_key = os.getenv('PINECONE_API_KEY')
cloud = os.getenv('PINECONE_CLOUD', 'aws')
region = os.getenv('PINECONE_REGION', 'us-east-1')

if not api_key:
    print("❌ PINECONE_API_KEY not found in environment")
    sys.exit(1)

try:
    # Initialize Pinecone
    pc = Pinecone(api_key=api_key)
    
    # List existing indexes
    existing_indexes = [index.name for index in pc.list_indexes()]
    
    if '${INDEX_NAME}' not in existing_indexes:
        # Create index on AWS (free tier available)
        pc.create_index(
            name='${INDEX_NAME}',
            dimension=1536,
            metric='cosine',
            spec=ServerlessSpec(
                cloud=cloud,
                region=region
            )
        )
        print(f"✅ Created Pinecone index: ${INDEX_NAME}")
        print(f"   Cloud: {cloud}, Region: {region}")
    else:
        print(f"ℹ️  Pinecone index already exists: ${INDEX_NAME}")
    
except Exception as e:
    print(f"❌ Pinecone setup failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
EOF

echo "✅ Pinecone setup complete"
