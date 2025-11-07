# Platform Demo Script

## 🎬 Complete Platform Demonstration

### Part 1: Data Discovery (Discovery Agent)
```bash
# Show service capabilities
curl http://localhost:8004/ | jq .

# Discover all Kafka topics
curl http://localhost:8004/discover | jq '.topics[] | {name: .name, messages: .message_count}'

# Get platform statistics
curl http://localhost:8004/stats | jq .

# Analyze specific topic
curl http://localhost:8004/topics/supply-chain.orders/analysis | jq .
```

### Part 2: AI-Powered Recommendations
```bash
# Generate recommendations
curl -X POST http://localhost:8004/recommendations/generate | jq .

# View all recommendations
curl http://localhost:8004/recommendations | jq '.[] | {type, confidence, impact}'

# Get recommendation statistics
curl http://localhost:8004/recommendations/stats | jq .
```

### Part 3: Multi-Provider AI
```bash
# Check provider health
curl http://localhost:8002/health | jq .

# Generate analysis with Claude
curl -X POST http://localhost:8002/v1/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Analyze Kafka topic utilization", "provider": "claude"}' | jq .
```

### Part 4: Documentation Search (MCP + RAG)
```bash
# Search via MCP Server
curl -X POST http://localhost:8003/tools/query_documentation \
  -H "Content-Type: application/json" \
  -d '{"question": "supply chain best practices", "max_results": 3}' | jq .
```

### Part 5: Live Data Flow
```bash
# Show data being generated
docker logs platform-event-producer --tail 10

# View in Kafka UI
open http://localhost:8080
# Navigate to: Topics → supply-chain.orders → Messages
```

