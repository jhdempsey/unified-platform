.PHONY: help setup build start stop restart status logs health clean \
        bootstrap deploy destroy \
        flink-start flink-stop flink-ui

# ==============================================================================
# UNIFIED PLATFORM - MAKEFILE
# Multi-Vertical Event-Driven ML/AI Platform
# ==============================================================================

# Configuration
VERTICAL ?= supply-chain
ENVIRONMENT ?= dev
GCP_PROJECT_ID ?= $(shell grep GCP_PROJECT_ID .env 2>/dev/null | cut -d'=' -f2)

help: ## Show this help message
	@echo "🚀 Unified ML/AI Platform"
	@echo ""
	@echo "📦 Setup & Build:"
	@echo "  make setup            Create .env file"
	@echo "  make build            Build all Docker images"
	@echo ""
	@echo "🎬 Local Development:"
	@echo "  make start            Start platform"
	@echo "  make stop             Stop platform"
	@echo "  make restart          Restart platform"
	@echo "  make status           Show service status"
	@echo "  make logs             Tail all logs"
	@echo "  make health           Check service health"
	@echo ""
	@echo "🚀 Deployment:"
	@echo "  make deploy-dev       Deploy to dev (local)"
	@echo "  make deploy-gcp-dev   Deploy to GCP dev"
	@echo "  make deploy-gcp-staging   Deploy to GCP staging"
	@echo "  make deploy-gcp-prod  Deploy to GCP prod"
	@echo ""
	@echo "🔧 Bootstrap:"
	@echo "  make bootstrap        Bootstrap platform (topics, schemas, etc.)"
	@echo ""
	@echo "🗑️  Teardown:"
	@echo "  make destroy-dev      Destroy dev environment"
	@echo "  make destroy-gcp-dev  Destroy GCP dev"
	@echo ""
	@echo "🌊 Flink:"
	@echo "  make flink-start      Start Flink cluster"
	@echo "  make flink-stop       Stop Flink cluster"
	@echo "  make flink-ui         Open Flink dashboard"
	@echo ""
	@echo "⚙️  Configuration:"
	@echo "  VERTICAL=$(VERTICAL)"
	@echo "  ENVIRONMENT=$(ENVIRONMENT)"
	@echo ""
	@echo "🌐 Access:"
	@echo "  Flink UI:       http://localhost:8085"
	@echo "  Kafka UI:       http://localhost:8080"
	@echo "  MLflow:         http://localhost:5001"
	@echo "  Grafana:        http://localhost:3002"
	@echo "  Dashboard:      http://localhost:8501"

# ==============================================================================
# SETUP & INSTALLATION
# ==============================================================================

setup: ## Setup local environment
	@echo "🔧 Setting up environment..."
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "✅ Created .env file"; \
		echo ""; \
		echo "📝 Next steps:"; \
		echo "  1. Edit .env with your API keys"; \
		echo "  2. Set VERTICAL=$(VERTICAL)"; \
		echo "  3. Run: make build"; \
	else \
		echo "ℹ️  .env file already exists"; \
	fi

build: ## Build all Docker images
	@echo "🏗️  Building images for vertical: $(VERTICAL)"
	@echo ""
	@echo "→ Building Flink..."
	@docker build -t flink-with-kafka:1.18 \
		-f core/infrastructure/docker/flink/Dockerfile \
		core/infrastructure/docker/flink/
	@echo ""
	@echo "→ Building core services..."
	@VERTICAL=$(VERTICAL) docker-compose build
	@echo ""
	@echo "✅ All images built for $(VERTICAL)"

# ==============================================================================
# LOCAL DEVELOPMENT
# ==============================================================================

start: ## Start all services locally
	@echo "🚀 Starting platform (vertical: $(VERTICAL))"
	@VERTICAL=$(VERTICAL) ENVIRONMENT=$(ENVIRONMENT) docker-compose up -d
	@echo ""
	@echo "⏳ Waiting for services..."
	@sleep 15
	@$(MAKE) status
	@echo ""
	@echo "✅ Platform started!"
	@echo ""
	@echo "🌐 Access services:"
	@echo "  Flink:      http://localhost:8085"
	@echo "  Kafka UI:   http://localhost:8080"
	@echo "  MLflow:     http://localhost:5001"
	@echo "  Grafana:    http://localhost:3002"
	@echo "  Dashboard:  http://localhost:8501"
	@echo ""
	@echo "📋 Next: make bootstrap (to create topics/schemas)"

stop: ## Stop all services
	@echo "🛑 Stopping platform..."
	@docker-compose down
	@echo "✅ Platform stopped"

restart: stop start ## Restart platform

status: ## Show service status
	@echo "📊 Service Status:"
	@docker-compose ps

logs: ## Tail all logs
	@docker-compose logs -f

logs-%: ## Tail specific service logs
	@docker-compose logs -f $*

health: ## Check service health
	@echo "🏥 Platform Health Check"
	@echo ""
	@echo "Event Streaming:"
	@curl -sf http://localhost:9092 > /dev/null 2>&1 && echo "  ✅ Kafka" || echo "  ❌ Kafka"
	@curl -sf http://localhost:8081/subjects > /dev/null 2>&1 && echo "  ✅ Schema Registry" || echo "  ❌ Schema Registry"
	@curl -sf http://localhost:8080 > /dev/null 2>&1 && echo "  ✅ Kafka UI" || echo "  ❌ Kafka UI"
	@echo ""
	@echo "Stream Processing:"
	@curl -sf http://localhost:8085/overview > /dev/null 2>&1 && echo "  ✅ Flink" || echo "  ❌ Flink"
	@echo ""
	@echo "ML/AI Services:"
	@curl -sf http://localhost:5001 > /dev/null 2>&1 && echo "  ✅ MLflow" || echo "  ❌ MLflow"
	@curl -sf http://localhost:8001/health > /dev/null 2>&1 && echo "  ✅ Model Inference" || echo "  ❌ Model Inference"
	@curl -sf http://localhost:8002/health > /dev/null 2>&1 && echo "  ✅ AI Gateway" || echo "  ❌ AI Gateway"
	@echo ""
	@echo "Observability:"
	@curl -sf http://localhost:9091/-/healthy > /dev/null 2>&1 && echo "  ✅ Prometheus" || echo "  ❌ Prometheus"
	@curl -sf http://localhost:3002/api/health > /dev/null 2>&1 && echo "  ✅ Grafana" || echo "  ❌ Grafana"

# ==============================================================================
# BOOTSTRAP
# ==============================================================================

bootstrap: ## Bootstrap platform (topics, schemas, Pinecone, MLflow)
	@echo "🔄 Bootstrapping platform for $(VERTICAL)"
	@bash scripts/bootstrap/bootstrap.sh $(ENVIRONMENT) $(VERTICAL)

# ==============================================================================
# FLINK COMMANDS
# ==============================================================================

flink-start: ## Start Flink cluster
	@echo "🌊 Starting Flink..."
	@docker-compose up -d flink-jobmanager flink-taskmanager
	@sleep 10
	@echo "✅ Flink started"
	@echo "   Dashboard: http://localhost:8085"

flink-stop: ## Stop Flink cluster
	@docker-compose stop flink-jobmanager flink-taskmanager

flink-ui: ## Open Flink dashboard
	@open http://localhost:8085 2>/dev/null || \
		xdg-open http://localhost:8085 2>/dev/null || \
		echo "Open: http://localhost:8085"

flink-logs: ## View Flink logs
	@docker logs platform-flink-jobmanager --tail=50

# ==============================================================================
# DEPLOYMENT
# ==============================================================================

deploy-dev: build start bootstrap ## Full local deployment
	@echo "✅ Dev environment ready!"
	@$(MAKE) health

deploy-gcp-dev: ## Deploy to GCP dev
	@echo "☁️  Deploying to GCP dev (vertical: $(VERTICAL))"
	@bash scripts/deployment/deploy-gke.sh dev $(VERTICAL)

deploy-gcp-staging: ## Deploy to GCP staging
	@echo "☁️  Deploying to GCP staging (vertical: $(VERTICAL))"
	@bash scripts/deployment/deploy-gke.sh staging $(VERTICAL)

deploy-gcp-prod: ## Deploy to GCP prod (blue/green)
	@echo "☁️  Deploying to GCP prod (vertical: $(VERTICAL))"
	@echo "⚠️  This will initiate blue/green deployment"
	@read -p "Continue? (yes/no): " confirm; \
	if [ "$$confirm" = "yes" ]; then \
		bash scripts/deployment/deploy-gke.sh prod $(VERTICAL); \
	else \
		echo "❌ Cancelled"; \
	fi

# ==============================================================================
# TEARDOWN
# ==============================================================================

destroy-dev: ## Destroy local dev environment
	@echo "⚠️  Destroying local dev environment"
	@read -p "Continue? (yes/no): " confirm; \
	if [ "$$confirm" = "yes" ]; then \
		bash scripts/teardown/backup-critical-data.sh dev; \
		docker-compose down -v; \
		echo "✅ Dev environment destroyed"; \
	else \
		echo "❌ Cancelled"; \
	fi

destroy-gcp-dev: ## Destroy GCP dev environment
	@echo "☁️  Destroying GCP dev"
	@bash scripts/teardown/backup-critical-data.sh dev
	@cd core/infrastructure/terraform/environments/dev && terraform destroy

destroy-gcp-staging: ## Destroy GCP staging environment
	@echo "☁️  Destroying GCP staging"
	@bash scripts/teardown/backup-critical-data.sh staging
	@cd core/infrastructure/terraform/environments/staging && terraform destroy

destroy-gcp-prod: ## Destroy GCP prod environment
	@echo "☁️  Destroying GCP prod"
	@echo "⚠️  WARNING: This will destroy production!"
	@read -p "Type 'DESTROY PROD' to confirm: " confirm; \
	if [ "$$confirm" = "DESTROY PROD" ]; then \
		bash scripts/teardown/backup-critical-data.sh prod; \
		cd core/infrastructure/terraform/environments/prod && terraform destroy; \
	else \
		echo "❌ Cancelled"; \
	fi

# ==============================================================================
# UTILITIES
# ==============================================================================

clean: ## Clean local artifacts
	@echo "🧹 Cleaning..."
	@docker-compose down -v
	@docker system prune -f
	@echo "✅ Cleaned"

shell-%: ## Open shell in container
	@docker exec -it platform-$* /bin/bash || docker exec -it platform-$* /bin/sh

ps: status ## Alias for status

.DEFAULT_GOAL := help
