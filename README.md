# Unified ML/AI Platform on Confluent

Enterprise-grade, event-driven ML/AI platform built on Kafka and Confluent technologies.

## 🚀 Quick Start
```bash
# Deploy complete platform (3-5 minutes)
make deploy-dev VERTICAL=supply-chain

# Check health
make health

# Access services
open http://localhost:8080   # Kafka UI
open http://localhost:8004/docs  # Discovery Agent API
open http://localhost:8501   # Dashboard
```

## 🎯 Platform Capabilities

### **Event Streaming** (Confluent Stack)
- Apache Kafka with KRaft mode
- Schema Registry with Avro schemas
- Kafka UI for management
- Live data simulation (45 events/sec)

### **Stream Processing**
- Apache Flink for real-time processing
- Stateful stream transformations
- Checkpointing and fault tolerance

### **ML/AI Services**
- **MLflow**: Experiment tracking & model registry
- **Model Inference**: Serve models via REST API
- **AI Gateway**: Multi-provider AI (Claude, GPT-4, Gemini)
- **RAG Service**: Pinecone + Anthropic for domain knowledge

### **Intelligent Agents**
- **Discovery Agent**: AI-powered data catalog
  - Auto-discover Kafka topics
  - Schema similarity analysis
  - Redundancy detection
  - Product recommendations
- **MCP Server**: Model Context Protocol
  - Tool integration
  - Documentation search via RAG

### **Data Services**
- **Event Producer**: Supply chain data simulator
  - Orders, suppliers, quality alerts
  - Configurable event rate
  - Realistic data generation

### **Observability**
- Prometheus metrics
- Grafana dashboards  
- Jaeger distributed tracing
- Complete platform telemetry

### **Dashboard**
- Supply Chain analytics
- Real-time KPIs
- ML model performance

## 📚 Documentation

- **[API Reference](docs/API_REFERENCE.md)**: Complete API documentation
- **[Demo Script](docs/DEMO_SCRIPT.md)**: Working demo scenarios
- **[Architecture](docs/ARCHITECTURE.md)**: System design (TODO)

## 🏗️ Architecture
```
┌─────────────────────────────────────────────────────────────┐
│                    Event Streaming Layer                     │
│  Kafka • Schema Registry • Flink Stream Processing          │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────┴───────────────────────────────┐
│                                                               │
│  ┌──────────────────┐      ┌───────────────────────────┐   │
│  │  Discovery Agent  │      │    ML/AI Services         │   │
│  │  • Auto-discover  │      │  • Model Inference        │   │
│  │  • AI recommend   │      │  • AI Gateway (multi-LLM) │   │
│  │  • Schema analyze │      │  • RAG Service            │   │
│  └──────────────────┘      └───────────────────────────┘   │
│                                                               │
│  ┌──────────────────┐      ┌───────────────────────────┐   │
│  │   MCP Server     │      │    Data Services          │   │
│  │  • Protocol tool │      │  • Event Producer         │   │
│  │  • RAG search    │      │  • Data Simulator         │   │
│  └──────────────────┘      └───────────────────────────┘   │
│                                                               │
└───────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────┴───────────────────────────────┐
│              Observability & Management                       │
│  Prometheus • Grafana • Jaeger • MLflow                      │
└───────────────────────────────────────────────────────────────┘
```

## 🛠️ Development

### Commands
```bash
make deploy-dev      # Deploy complete platform
make stop           # Stop without destroying
make start          # Resume stopped platform
make destroy-dev    # Teardown with backups
make bootstrap      # Initialize data
make health         # Health check
make logs SERVICE=<name>  # View logs
```

### Service URLs
| Service | URL | Purpose |
|---------|-----|---------|
| Kafka UI | http://localhost:8080 | Browse topics/messages |
| Discovery Agent | http://localhost:8004 | Data catalog API |
| AI Gateway | http://localhost:8002 | Multi-provider AI |
| MCP Server | http://localhost:8003 | Protocol tools |
| MLflow | http://localhost:5001 | ML experiments |
| Dashboard | http://localhost:8501 | Analytics |
| Grafana | http://localhost:3002 | Metrics |
| Prometheus | http://localhost:9091 | Monitoring |

### Adding New Verticals
```bash
# Copy template
cp -r templates/supply-chain templates/retail

# Customize for vertical
# - Update topics in bootstrap/init-topics.sh
# - Update schemas in bootstrap/schemas/
# - Update models in models/

# Deploy
make deploy-dev VERTICAL=retail
```

## 🚀 Deployment

### Local (Docker Compose)
```bash
make deploy-dev
```

### GCP/GKE
```bash
# Use Kubernetes manifests
kubectl apply -f core/infrastructure/kubernetes/

# Or use Terraform
cd terraform/gcp
terraform init
terraform apply
```

## 📊 Platform Statistics

- **18 Services**: All containerized and orchestrated
- **16 ML Model Files**: Ready for training/serving
- **5 Kafka Topics**: Auto-created on bootstrap
- **5 Avro Schemas**: Registered automatically
- **3 MLflow Experiments**: Supply chain models
- **1 Pinecone Index**: RAG knowledge base

## 🎯 Use Cases

### Confluent Customer Demos
- Event-driven ML/AI architecture
- Real-time data governance
- AI-powered data discovery
- Multi-provider AI gateway
- Complete observability

### Development Platform
- Rapid prototyping
- ML experiment tracking
- Model deployment pipeline
- Multi-vertical support

### Production Deployment
- Kubernetes-ready
- Environment-aware config
- Secret management
- Disaster recovery

## 🏆 What Makes This Special

✅ **Complete Automation**: Zero to running in 3-5 minutes  
✅ **Production-Grade**: Full observability, fault tolerance  
✅ **AI-Powered**: Intelligent agents, multi-provider LLMs  
✅ **Multi-Vertical**: Template-based expansion  
✅ **Developer-Friendly**: Simple commands, clear docs  
✅ **Confluent Native**: Built on Kafka ecosystem  

## 📝 License

[Your License Here]

## 🤝 Contributing

[Contributing Guidelines Here]

---

**Built with ❤️ for the Confluent ecosystem**
