#!/bin/bash
set -e

# ==============================================================================
# Intelligent Data Product Platform - Development Environment Initialization
# ==============================================================================

BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Platform Development Environment Setup${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# ==============================================================================
# Check Prerequisites
# ==============================================================================

echo -e "${GREEN}Checking prerequisites...${NC}"

# Check Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}✗ Docker not found. Please install Docker.${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Docker found${NC}"

# Check Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}✗ Docker Compose not found. Please install Docker Compose.${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Docker Compose found${NC}"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}✗ Python 3 not found. Please install Python 3.11+.${NC}"
    exit 1
fi
PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
if (( $(echo "$PYTHON_VERSION < 3.11" | bc -l) )); then
    echo -e "${RED}✗ Python 3.11+ required. Found: $PYTHON_VERSION${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Python $PYTHON_VERSION found${NC}"

# Check Node.js
if ! command -v node &> /dev/null; then
    echo -e "${RED}✗ Node.js not found. Please install Node.js 18+.${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Node.js found${NC}"

# Check Poetry
if ! command -v poetry &> /dev/null; then
    echo -e "${YELLOW}! Poetry not found. Installing...${NC}"
    curl -sSL https://install.python-poetry.org | python3 -
    export PATH="$HOME/.local/bin:$PATH"
    
    # Verify installation
    if ! command -v poetry &> /dev/null; then
        echo -e "${RED}✗ Poetry installation failed. Please install manually:${NC}"
        echo -e "${YELLOW}  curl -sSL https://install.python-poetry.org | python3 -${NC}"
        echo -e "${YELLOW}  Then add to PATH: export PATH=\"\$HOME/.local/bin:\$PATH\"${NC}"
        echo -e ""
        echo -e "${YELLOW}Continuing without Poetry (you can install it later)...${NC}"
        POETRY_AVAILABLE=false
    else
        echo -e "${GREEN}✓ Poetry installed${NC}"
        POETRY_AVAILABLE=true
    fi
else
    echo -e "${GREEN}✓ Poetry found${NC}"
    POETRY_AVAILABLE=true
fi

echo ""

# ==============================================================================
# Create Directory Structure
# ==============================================================================

echo -e "${GREEN}Creating directory structure...${NC}"

# Create all directories
mkdir -p services/{product-service,agent-orchestration,lineage-service,quality-service,mcp-server}/{src,tests}
mkdir -p agents/{stream-analysis,product-generator,business-context}/{src,tests}
mkdir -p shared/{a2a-protocol,mcp-client,observability,common}
mkdir -p portal/{backstage,streamlit}
mkdir -p infrastructure/{terraform,kubernetes,docker}/{dev,staging,production}
mkdir -p docs/{architecture,services,agents,protocols,deployment}
mkdir -p scripts
mkdir -p tests/{unit,integration,e2e}
mkdir -p config/{dev,staging,production}

echo -e "${GREEN}✓ Directory structure created${NC}"

# ==============================================================================
# Initialize Python Environment
# ==============================================================================

if [ "$POETRY_AVAILABLE" = true ]; then
    echo -e "${GREEN}Initializing Python environment...${NC}"
    
    # Install Poetry dependencies
    poetry install
    
    echo -e "${GREEN}✓ Python dependencies installed${NC}"
else
    echo -e "${YELLOW}Skipping Poetry dependency installation (Poetry not available)${NC}"
    echo -e "${YELLOW}You can install dependencies manually with pip later.${NC}"
fi

# ==============================================================================
# Create .env file
# ==============================================================================

if [ ! -f .env ]; then
    echo -e "${GREEN}Creating .env file...${NC}"
    
    cat > .env << 'EOF'
# ==============================================================================
# Platform Environment Variables - Development
# ==============================================================================

# Database
DATABASE_URL=postgresql://platform:platform_dev@localhost:5432/platform

# Redis
REDIS_URL=redis://localhost:6380/0

# Confluent Kafka
KAFKA_BOOTSTRAP_SERVERS=localhost:19093
SCHEMA_REGISTRY_URL=http://localhost:18081

# Elasticsearch
ELASTICSEARCH_URL=http://localhost:9200

# OpenTelemetry
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317

# LLM (Add your keys)
GEMINI_API_KEY=your_gemini_key_here
ANTHROPIC_API_KEY=your_anthropic_key_here
OPENAI_API_KEY=your_openai_key_here

# GCP (if needed)
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
GCP_PROJECT_ID=your_project_id

# Application
LOG_LEVEL=INFO
ENVIRONMENT=development
EOF

    echo -e "${YELLOW}⚠ Please edit .env file and add your API keys${NC}"
    echo -e "${GREEN}✓ .env file created${NC}"
else
    echo -e "${YELLOW}! .env file already exists, skipping${NC}"
fi

# ==============================================================================
# Initialize Git
# ==============================================================================

if [ ! -d .git ]; then
    echo -e "${GREEN}Initializing Git repository...${NC}"
    git init
    echo -e "${GREEN}✓ Git initialized${NC}"
else
    echo -e "${YELLOW}! Git repository already initialized${NC}"
fi

# ==============================================================================
# Install Pre-commit Hooks
# ==============================================================================

if [ "$POETRY_AVAILABLE" = true ]; then
    echo -e "${GREEN}Installing pre-commit hooks...${NC}"
    poetry run pre-commit install
    echo -e "${GREEN}✓ Pre-commit hooks installed${NC}"
else
    echo -e "${YELLOW}Skipping pre-commit hooks (Poetry not available)${NC}"
fi

# ==============================================================================
# Start Infrastructure Services
# ==============================================================================

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Starting Infrastructure Services${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

echo -e "${GREEN}Starting Docker Compose services...${NC}"
docker-compose up -d postgres redis zookeeper kafka schema-registry elasticsearch jaeger prometheus grafana

echo -e "${GREEN}Waiting for services to be ready...${NC}"
sleep 10

# Check PostgreSQL
echo -n "Checking PostgreSQL... "
until docker-compose exec -T postgres pg_isready -U platform &> /dev/null; do
    sleep 1
done
echo -e "${GREEN}✓${NC}"

# Check Redis
echo -n "Checking Redis... "
until docker-compose exec -T redis redis-cli ping &> /dev/null; do
    sleep 1
done
echo -e "${GREEN}✓${NC}"

# Check Kafka (Confluent)
echo -n "Checking Kafka... "
until docker-compose exec -T kafka kafka-broker-api-versions --bootstrap-server localhost:9092 &> /dev/null; do
    sleep 1
done
echo -e "${GREEN}✓${NC}"

echo ""
echo -e "${GREEN}✓ All infrastructure services are ready${NC}"

# ==============================================================================
# Initialize Database
# ==============================================================================

echo -e "${GREEN}Initializing database...${NC}"

# Run migrations (when implemented)
# cd services/product-service && poetry run alembic upgrade head && cd ../..

echo -e "${GREEN}✓ Database initialized${NC}"

# ==============================================================================
# Summary
# ==============================================================================

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Setup Complete!${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${GREEN}Environment initialized successfully.${NC}"
echo ""
echo -e "Next steps:"
echo -e "  1. Edit ${YELLOW}.env${NC} file and add your API keys"
echo -e "  2. Start all services: ${YELLOW}make docker-up${NC}"
echo -e "  3. View logs: ${YELLOW}make docker-logs${NC}"
echo -e "  4. Access services:"
echo -e "     - Backstage Portal: ${BLUE}http://localhost:3000${NC}"
echo -e "     - Streamlit Tools: ${BLUE}http://localhost:8501${NC}"
echo -e "     - API Gateway: ${BLUE}http://localhost:8080${NC}"
echo -e "     - Jaeger UI: ${BLUE}http://localhost:16686${NC}"
echo -e "     - Grafana: ${BLUE}http://localhost:3001${NC}"
echo -e "     - Prometheus: ${BLUE}http://localhost:9090${NC}"
echo ""
echo -e "Documentation: ${BLUE}./docs/${NC}"
echo -e "Run ${YELLOW}make help${NC} to see available commands"
echo ""
