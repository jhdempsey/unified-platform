# Unified Platform - API Reference

## 🎯 Quick Access
- **Discovery Agent:** http://localhost:8004/docs
- **Model Inference:** http://localhost:8001/docs
- **AI Gateway:** http://localhost:8002/docs
- **MCP Server:** http://localhost:8003 (no docs UI)
- **RAG Service:** http://localhost:8005/docs

---

## 1️⃣ Discovery Agent (Port 8004)

**Purpose:** AI-powered data catalog with topic discovery, schema analysis, and product recommendations

### Key Endpoints
```bash
# Get service info
curl http://localhost:8004/

# Health check
curl http://localhost:8004/health

# Discover all Kafka topics
curl http://localhost:8004/discover | jq .

# Search topics
curl -X POST http://localhost:8004/search \
  -H "Content-Type: application/json" \
  -d '{"query": "order", "limit": 10}' | jq .

# Get topic analysis
curl http://localhost:8004/topics/supply-chain.orders/analysis | jq .

# Get statistics
curl http://localhost:8004/stats | jq .

# Generate AI recommendations
curl -X POST http://localhost:8004/recommendations/generate | jq .

# Get recommendation stats
curl http://localhost:8004/recommendations/stats | jq .

# View all recommendations
curl http://localhost:8004/recommendations | jq .

# Approve a recommendation
curl -X POST http://localhost:8004/recommendations/{rec_id}/approve | jq .

# Promote to managed product
curl -X POST http://localhost:8004/promote \
  -H "Content-Type: application/json" \
  -d '{"topic_name": "supply-chain.orders"}' | jq .
```

**Full API Docs:** http://localhost:8004/docs

---

## 2️⃣ AI Gateway (Port 8002)

**Purpose:** Unified interface for multiple AI providers (Claude, GPT-4, Gemini)

### Key Endpoints
```bash
# Health check (shows provider status)
curl http://localhost:8002/health | jq .

# Generate with Claude
curl -X POST http://localhost:8002/v1/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Analyze supply chain efficiency",
    "provider": "claude",
    "max_tokens": 500
  }' | jq .

# Generate with GPT-4
curl -X POST http://localhost:8002/v1/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Forecast demand trends",
    "provider": "gpt4"
  }' | jq .

# Generate with Gemini
curl -X POST http://localhost:8002/v1/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Optimize inventory levels",
    "provider": "gemini"
  }' | jq .
```

**Full API Docs:** http://localhost:8002/docs

---

## 3️⃣ MCP Server (Port 8003)

**Purpose:** Model Context Protocol server for tool integration (RAG-powered documentation search)

### Available Endpoints
```bash
# Health check
curl http://localhost:8003/health | jq .

# List available tools
curl http://localhost:8003/tools | jq .

# Query documentation (RAG)
curl -X POST http://localhost:8003/tools/query_documentation \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What are the optimal reorder points for inventory?",
    "max_results": 3
  }' | jq .
```

**Note:** MCP Server doesn't have `/docs` UI. Use `/tools` to discover available tools.

---

## 4️⃣ Model Inference (Port 8001)

**Purpose:** ML model serving with MLflow integration

### Key Endpoints
```bash
# Health check
curl http://localhost:8001/health | jq .

# List available models
curl http://localhost:8001/models | jq .

# Make prediction (check /docs for exact schema)
curl -X POST http://localhost:8001/predict \
  -H "Content-Type: application/json" \
  -d '{
    "model_name": "demand-forecasting",
    "data": {...}
  }' | jq .
```

**Full API Docs:** http://localhost:8001/docs

---

## 5️⃣ RAG Service (Port 8005)

**Purpose:** Retrieval-Augmented Generation with Pinecone + Anthropic

### Key Endpoints
```bash
# Health check
curl http://localhost:8005/health | jq .

# Query (check /docs for exact endpoint name)
curl -X POST http://localhost:8005/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "optimal reorder points",
    "top_k": 5
  }' | jq .
```

**Full API Docs:** http://localhost:8005/docs

---

## 🎯 Demo Scenarios

### Scenario 1: Complete Data Discovery Flow
```bash
# 1. Discover all topics
curl http://localhost:8004/discover | jq '.topics | length'

# 2. Analyze specific topic
curl http://localhost:8004/topics/supply-chain.orders/analysis | jq .

# 3. Generate AI recommendations
curl -X POST http://localhost:8004/recommendations/generate | jq .

# 4. View recommendations
curl http://localhost:8004/recommendations | jq '.[] | {id, type, confidence}'
```

### Scenario 2: AI-Powered Analysis
```bash
# Use AI Gateway to analyze discovered data
curl -X POST http://localhost:8002/v1/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Based on the discovered Kafka topics, recommend data quality improvements",
    "provider": "claude"
  }' | jq .
```

### Scenario 3: Documentation Search via MCP
```bash
# Search for supply chain best practices
curl -X POST http://localhost:8003/tools/query_documentation \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What are supply chain compliance requirements?",
    "max_results": 5
  }' | jq .
```

