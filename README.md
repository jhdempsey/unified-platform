# Unified Platform

Enterprise-grade, event-driven ML/AI platform built on Confluent Cloud and Google Cloud Platform.

## 🎯 Overview

This platform consolidates AI-powered services, stream processing with Confluent Cloud Flink, and developer tooling into a unified event-driven architecture.

**Key Technologies:**
- **Stream Processing**: Confluent Cloud (Kafka, Flink, Schema Registry)
- **Compute**: Google Cloud Run (14 microservices)
- **ML/AI**: Claude, MLflow, scikit-learn
- **Infrastructure**: Terraform, Docker

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Confluent Cloud (Azure)                            │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │                         Kafka Cluster                                   │ │
│  │   order-events │ product-events │ supplier-events │ supply-chain.*     │ │
│  └────────────────────────────────┬────────────────────────────────────────┘ │
│                                   │                                          │
│  ┌────────────────────────────────▼────────────────────────────────────────┐ │
│  │                      Flink Compute Pool                                 │ │
│  │   Real-time Aggregations │ Stream Joins │ Anomaly Detection │ Alerts   │ │
│  └────────────────────────────────┬────────────────────────────────────────┘ │
│                                   │                                          │
│  ┌────────────────────────────────▼────────────────────────────────────────┐ │
│  │                       Schema Registry                                   │ │
│  │                    Avro schemas for all topics                          │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
└───────────────────────────────────┬─────────────────────────────────────────┘
                                    │ SASL_SSL
┌───────────────────────────────────▼─────────────────────────────────────────┐
│                         Google Cloud Platform                                │
│                                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │   Dashboard  │  │  Backstage   │  │    MLflow    │  │  AI Gateway  │    │
│  │  (Streamlit) │  │    (IDP)     │  │  (Tracking)  │  │ (Multi-LLM)  │    │
│  └──────┬───────┘  └──────────────┘  └───────┬──────┘  └──────┬───────┘    │
│         │                                     │                 │            │
│  ┌──────▼───────┐  ┌──────────────┐  ┌───────▼──────┐  ┌──────▼───────┐    │
│  │    Model     │  │ Supply Chain │  │   Product    │  │     RAG      │    │
│  │  Inference   │  │    Agent     │  │  Generator   │  │   Service    │    │
│  │  (sklearn)   │  │  (Claude)    │  │    (AI)      │  │  (Pinecone)  │    │
│  └──────────────┘  └──────┬───────┘  └──────────────┘  └──────────────┘    │
│                           │                                                  │
│         ┌─────────────────┼─────────────────┐                               │
│         ▼                 ▼                 ▼                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                      │
│  │    Event     │  │    Stream    │  │      ML      │◄─── Redis            │
│  │   Producer   │  │   Analysis   │  │   Consumer   │     (Cache)          │
│  └──────────────┘  └──────────────┘  └──────────────┘                      │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │  Infrastructure: VPC │ Cloud NAT │ Cloud SQL │ GCS │ Secret Manager  │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Local Development (Docker Compose)
```bash
# Deploy complete platform locally (3-5 minutes)
make deploy-dev VERTICAL=supply-chain

# Check health
make health

# Access services
open http://localhost:8501   # Dashboard
open http://localhost:8080   # Kafka UI
open http://localhost:5000   # MLflow
```

### Cloud Deployment (GCP + Confluent)
```bash
# Deploy to GCP
cd core/infrastructure/terraform/gcp-modules
terraform init
terraform apply

# Setup Confluent Cloud Flink (see docs/CONFLUENT_FLINK_SETUP.md)
```

## 📦 Services

### Cloud Run Services (14)

| Service | Port | Description |
|---------|------|-------------|
| **dashboard** | 8501 | Streamlit UI - platform monitoring, ML predictions |
| **backstage** | 7007 | Developer portal (IDP) - service catalog |
| **mlflow** | 8080 | ML experiment tracking and model registry |
| **model-inference** | 8001 | ML predictions (Random Forest fulfillment model) |
| **supply-chain-agent** | 8080 | AI agent with 7 tools (Claude-powered) |
| **product-generator** | 8003 | AI-powered product/schema generation |
| **product-service** | 8001 | Product CRUD REST API |
| **ai-gateway** | 8080 | Multi-LLM gateway (Anthropic, OpenAI, Gemini) |
| **rag-service** | 8080 | Document Q&A with Pinecone vector store |
| **event-producer** | 8080 | Kafka event generation for testing |
| **stream-analysis** | 8080 | Real-time stream monitoring and alerts |
| **ml-consumer** | 8080 | Kafka consumer with Redis prediction caching |
| **discovery-agent** | 8004 | Kafka topic and schema discovery |
| **mcp-server** | 8080 | Model Context Protocol tools |

### Confluent Cloud Components

| Component | Purpose |
|-----------|---------|
| **Kafka Cluster** | Event streaming backbone |
| **Flink Compute Pool** | Real-time stream processing |
| **Schema Registry** | Avro schema management |

### GCP Infrastructure

| Component | Type | Purpose |
|-----------|------|---------|
| Cloud SQL | PostgreSQL | MLflow metadata |
| Memorystore | Redis | ML prediction caching |
| Cloud Storage | GCS | ML model artifacts |
| VPC + Cloud NAT | Network | Secure connectivity |
| Artifact Registry | Docker | Container images |
| Secret Manager | Secrets | API keys and credentials |

## 🔧 Setup Instructions

### Prerequisites

- Google Cloud Platform account with billing
- Confluent Cloud account
- API Keys: Anthropic, OpenAI (optional), Gemini (optional), Pinecone
- Tools: Docker, Terraform >= 1.0, gcloud CLI

### 1. Configure Secrets

Create secrets in Google Secret Manager:

```bash
# AI Provider Keys
gcloud secrets create anthropic-api-key --data-file=- <<< "your-key"
gcloud secrets create openai-api-key --data-file=- <<< "your-key"
gcloud secrets create gemini-api-key --data-file=- <<< "your-key"
gcloud secrets create pinecone-api-key --data-file=- <<< "your-key"

# Confluent Cloud (from your cluster settings)
gcloud secrets create confluent-bootstrap-server --data-file=- <<< "pkc-xxxxx.region.provider.confluent.cloud:9092"
gcloud secrets create confluent-kafka-api-key --data-file=- <<< "your-api-key"
gcloud secrets create confluent-kafka-api-secret --data-file=- <<< "your-api-secret"
gcloud secrets create confluent-schema-registry-url --data-file=- <<< "https://psrc-xxxxx.region.provider.confluent.cloud"
gcloud secrets create confluent-sr-api-key --data-file=- <<< "your-sr-key"
gcloud secrets create confluent-sr-api-secret --data-file=- <<< "your-sr-secret"
```

### 2. Deploy GCP Infrastructure

```bash
cd core/infrastructure/terraform/gcp-modules

# Initialize
terraform init

# Configure
export TF_VAR_project_id="your-gcp-project-id"
export TF_VAR_region="us-central1"

# Deploy
terraform plan
terraform apply
```

### 3. Build and Deploy Services

```bash
# Authenticate Docker
gcloud auth configure-docker us-central1-docker.pkg.dev

# Build and push all services
PROJECT_ID="your-project-id"
REGISTRY="us-central1-docker.pkg.dev/$PROJECT_ID/ai-platform-repo"

for service in dashboard ml-consumer model-inference supply-chain-agent \
               event-producer stream-analysis product-generator; do
  docker build --platform linux/amd64 \
    -t $REGISTRY/$service:latest \
    -f core/services/$service/Dockerfile \
    core/services/$service/
  docker push $REGISTRY/$service:latest
done

# Apply to Cloud Run
terraform apply
```

### 4. Setup Confluent Cloud Flink

See [docs/CONFLUENT_FLINK_SETUP.md](docs/CONFLUENT_FLINK_SETUP.md) for detailed instructions.

**Quick setup:**
1. Create Flink compute pool in Confluent Cloud UI
2. Open SQL workspace
3. Run the provided Flink SQL statements
4. Verify topics are created

## 🤖 Supply Chain Agent

The AI agent provides a conversational interface to the platform:

```bash
# Chat with the agent
curl -X POST https://supply-chain-agent-PROJECT.REGION.run.app/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What Kafka topics are available?"}'
```

**7 Integrated Tools:**
| Tool | Description |
|------|-------------|
| `search_documents` | RAG-based knowledge search |
| `list_products` | Product catalog listing |
| `get_product` | Product details by ID |
| `discover_kafka_topics` | Kafka topic discovery |
| `get_stream_stats` | Stream processing statistics |
| `get_ml_predictions_stats` | ML consumer metrics |
| `generate_product` | AI-powered product generation |

## 📊 Kafka Topics

### Source Topics (Event Producer)
| Topic | Description |
|-------|-------------|
| `order-events` | Customer orders |
| `product-events` | Product catalog changes |
| `supplier-events` | Supplier updates |

### Flink Output Topics
| Topic | Description |
|-------|-------------|
| `supply-chain.orders-aggregated` | Orders per minute by region |
| `supply-chain.hourly-revenue` | Hourly revenue statistics |
| `supply-chain.enriched-orders` | Orders joined with products |
| `supply-chain.alerts` | Low stock and anomaly alerts |
| `supply-chain.predictions` | Rolling stats for ML |

## 🧪 API Examples

### ML Predictions
```bash
curl -X POST https://model-inference-PROJECT.REGION.run.app/predict/demand \
  -H "Content-Type: application/json" \
  -d '{
    "product_category": 1,
    "order_quantity": 100,
    "warehouse_distance": 50.0,
    "day_of_week": 3,
    "season": 2,
    "supplier_reliability": 85.0,
    "weather_condition": 0
  }'
```

### Generate Events
```bash
curl -X POST https://event-producer-PROJECT.REGION.run.app/produce \
  -H "Content-Type: application/json" \
  -d '{"topic": "order-events", "count": 10}'
```

### Stream Statistics
```bash
curl https://stream-analysis-PROJECT.REGION.run.app/stats
```

## 🛠️ Local Development

### Docker Compose Services

```bash
# Start all services
docker-compose up -d

# View logs
make logs SERVICE=ml-consumer

# Stop
make stop

# Destroy
make destroy-dev
```

### Local Service URLs
| Service | URL |
|---------|-----|
| Dashboard | http://localhost:8501 |
| Kafka UI | http://localhost:8080 |
| MLflow | http://localhost:5000 |
| Model Inference | http://localhost:8001 |
| Discovery Agent | http://localhost:8004 |
| AI Gateway | http://localhost:8002 |
| Grafana | http://localhost:3000 |
| Prometheus | http://localhost:9090 |
| Jaeger | http://localhost:16686 |

## 📁 Project Structure

```
unified-platform/
├── core/
│   ├── services/                 # Microservices
│   │   ├── dashboard/            # Streamlit UI
│   │   ├── ml-consumer/          # Kafka consumer + Redis
│   │   ├── model-inference/      # ML predictions
│   │   ├── supply-chain-agent/   # AI agent (Claude)
│   │   ├── event-producer/       # Event generation
│   │   ├── stream-analysis/      # Stream monitoring
│   │   ├── product-generator/    # AI product creation
│   │   ├── ai-gateway/           # Multi-LLM gateway
│   │   ├── rag-service/          # Document Q&A
│   │   ├── mcp-server/           # MCP tools
│   │   └── mlflow/               # ML tracking
│   ├── ml/
│   │   └── models/               # ML model code
│   └── infrastructure/
│       ├── terraform/
│       │   └── gcp-modules/      # GCP Terraform
│       └── docker/               # Docker configs
├── templates/
│   └── supply-chain/             # Domain templates
├── docs/
│   ├── CONFLUENT_FLINK_SETUP.md  # Flink setup guide
│   └── API_REFERENCE.md          # API documentation
├── docker-compose.yml            # Local development
└── Makefile                      # Build commands
```

## 💰 Cost Estimates

### GCP (Monthly)
| Resource | Cost |
|----------|------|
| Cloud Run (14 services) | $50-150 |
| Cloud SQL (db-f1-micro) | $30-50 |
| Memorystore Redis (1GB) | $35 |
| Cloud NAT | $30 |
| Cloud Storage | $5 |
| **Subtotal** | **~$150-270** |

### Confluent Cloud (Monthly)
| Resource | Cost |
|----------|------|
| Kafka Cluster (Basic) | $50-200 |
| Flink (5 CFUs) | ~$250 |
| Schema Registry | Included |
| **Subtotal** | **~$300-450** |

**Total Estimated: $450-720/month**

### Cost Optimization Tips
- Set `min_instance_count = 0` for dev/test services
- Use smaller Cloud SQL instance
- Start with 5 Flink CFUs, scale as needed
- Use Basic Kafka cluster for development

## 🐛 Troubleshooting

### Cloud Run Service Won't Start
```bash
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=SERVICE_NAME" --limit=20
```

### Kafka Connection Issues
- Verify secrets have no trailing whitespace/newlines
- Check VPC egress allows outbound traffic
- Ensure SASL_SSL authentication configured

### Flink Statements Not Processing
- Verify source topics have data
- Check watermark configuration
- Ensure CFU capacity available

### Cold Start Timeouts
- Increase startup probe timeout
- Set `min_instance_count = 1` for critical services

## 📚 Documentation

- [Confluent Cloud Flink Setup](docs/CONFLUENT_FLINK_SETUP.md)
- [API Reference](docs/API_REFERENCE.md)
- [Demo Script](docs/DEMO_SCRIPT.md)

## 🤝 Contributing

1. Create feature branch
2. Test locally with Docker Compose
3. Build and push images
4. Run `terraform plan`
5. Submit pull request

## 📜 License

[Your License Here]

---

**Built for event-driven AI/ML on Confluent Cloud and Google Cloud Platform**
