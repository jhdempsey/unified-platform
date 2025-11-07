# Getting Started

## Prerequisites
- Docker Desktop
- Python 3.11+
- Make

## Setup Steps

### 1. Install Bootstrap Dependencies
```bash
pip install -r scripts/requirements.txt
```

This installs tools needed for:
- Creating Kafka topics
- Registering schemas
- Setting up Pinecone
- Initializing MLflow

### 2. Configure Environment
```bash
make setup
nano .env  # Add your API keys
```

### 3. Deploy Platform
```bash
make deploy-dev VERTICAL=supply-chain
```

This will:
- Build all images
- Start all services
- Run bootstrap automatically

### 4. Verify
```bash
make health
open http://localhost:8501  # Dashboard
```

## Troubleshooting

**Bootstrap fails?**
- Ensure `scripts/requirements.txt` is installed
- Check API keys in `.env`
- Verify services are running: `docker-compose ps`
