# Unified ML/AI Platform

**Multi-Vertical Event-Driven ML/AI Platform for Confluent Customers**

## 🎯 Overview

This platform enables Confluent customers to build AI-powered data products through an event-driven architecture. It provides a core platform with pluggable vertical templates.

### Architecture

```
┌─────────────────────────────────────────────────────────┐
│              CORE PLATFORM (Universal)                   │
│  • Event streaming (Kafka)                              │
│  • Stream processing (Flink)                            │
│  • Discovery & AI-assisted product creation             │
│  • ML infrastructure (MLflow, serving)                  │
│  • Observability                                        │
└─────────────────────────────────────────────────────────┘
                          ↕
┌─────────────────────────────────────────────────────────┐
│           VERTICAL TEMPLATES (Pluggable)                 │
│  • Supply Chain (reference implementation)              │
│  • Financial Services (future)                          │
│  • Retail (future)                                      │
│  • Entertainment (future)                               │
└─────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

```bash
# Setup environment
make setup
# Edit .env with your API keys and vertical selection

# Build all images
make build

# Deploy with supply chain vertical
make deploy-dev VERTICAL=supply-chain

# Check health
make health
```

## 📂 Project Structure

```
unified-platform/
├── core/                    # Core platform (universal)
├── templates/               # Vertical templates
│   └── supply-chain/       # Reference implementation
├── deployments/            # Environment configs
├── scripts/                # Automation scripts
└── docs/                   # Documentation
```

## 📖 Documentation

- [Architecture Guide](docs/architecture/)
- [Creating Vertical Templates](docs/guides/creating-templates.md)
- [Deployment Guide](docs/guides/deployment.md)
- [Supply Chain Template](templates/supply-chain/README.md)

## 🔧 Development

Run `make help` for all available commands.

## 🎯 4-Step Workflow

1. **Discovery**: Scan Kafka topics, infer schemas
2. **AI Analysis**: Detect patterns, propose data products
3. **Human Review**: Approve/refine in UI
4. **Materialization**: Deploy Flink jobs, create topics

## 🌐 Supported Verticals

- ✅ Supply Chain (reference implementation)
- 🔮 Financial Services (coming soon)
- 🔮 Retail (coming soon)
- 🔮 Entertainment (coming soon)

## 🔧 Developer Setup

### Prerequisites
- Docker & Docker Compose
- Python 3.11+
- Make

### Installation

1. **Clone repository**
```bash
   git clone <repo>
   cd unified-platform
```

2. **Install bootstrap dependencies**
```bash
   pip install -r scripts/requirements.txt
```

3. **Configure environment**
```bash
   make setup
   # Edit .env with your API keys
```

4. **Deploy locally**
```bash
   make deploy-dev
```
