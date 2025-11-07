# Platform Mono-Repo Directory Structure

## Overview

```
platform/
├── services/              # Backend microservices
├── agents/                # Intelligent agents
├── shared/                # Shared libraries
├── portal/                # User interfaces
├── infrastructure/        # IaC and deployment configs
├── docs/                  # Documentation
├── scripts/               # Automation scripts
├── tests/                 # Integration tests
├── config/                # Configuration files
└── [root files]           # Project configs
```

---

## Detailed Structure

### `/services` - Backend Microservices

```
services/
├── product-service/           # Data product CRUD & catalog
│   ├── src/
│   │   ├── api/              # FastAPI routes
│   │   ├── models/           # SQLAlchemy models
│   │   ├── schemas/          # Pydantic schemas
│   │   ├── services/         # Business logic
│   │   └── main.py           # Application entry
│   ├── tests/
│   ├── alembic/              # Database migrations
│   ├── Dockerfile
│   ├── pyproject.toml
│   └── README.md
│
├── agent-orchestration/       # LangGraph workflows & A2A routing
│   ├── src/
│   │   ├── workflows/        # LangGraph definitions
│   │   ├── router/           # A2A message router
│   │   └── main.py
│   ├── tests/
│   ├── Dockerfile
│   └── README.md
│
├── lineage-service/           # OpenLineage integration
│   ├── src/
│   │   ├── collectors/       # Lineage data collectors
│   │   ├── graph/            # Graph storage & queries
│   │   └── main.py
│   ├── tests/
│   └── Dockerfile
│
├── quality-service/           # Great Expectations & monitoring
│   ├── src/
│   │   ├── expectations/     # Quality expectations
│   │   ├── monitoring/       # Quality monitoring
│   │   └── main.py
│   ├── tests/
│   └── Dockerfile
│
└── mcp-server/                # Model Context Protocol gateway
    ├── src/
    │   ├── tools/            # MCP tool implementations
    │   ├── registry/         # Tool registry
    │   └── main.py
    ├── tests/
    └── Dockerfile
```

### `/agents` - Intelligent Agents

```
agents/
├── stream-analysis/           # Observes Kafka, suggests products
│   ├── src/
│   │   ├── analyzers/        # Stream analysis logic
│   │   ├── detectors/        # Pattern detection
│   │   └── main.py
│   ├── tests/
│   ├── Dockerfile
│   └── README.md
│
├── product-generator/         # Generates schemas, code, docs
│   ├── src/
│   │   ├── generators/       # Code generators
│   │   │   ├── schema_gen.py
│   │   │   ├── dbt_gen.py
│   │   │   └── terraform_gen.py
│   │   └── main.py
│   ├── templates/            # Code templates
│   ├── tests/
│   └── Dockerfile
│
└── business-context/          # RAG-based policy validation
    ├── src/
    │   ├── rag/              # RAG implementation
    │   ├── validators/       # Policy validators
    │   └── main.py
    ├── knowledge_base/       # Policy documents
    ├── tests/
    └── Dockerfile
```

### `/shared` - Shared Libraries

```
shared/
├── a2a-protocol/              # Agent-to-Agent communication
│   ├── a2a_protocol.py       # Protocol implementation
│   ├── examples.py           # Usage examples
│   ├── tests/
│   └── README.md
│
├── mcp-client/                # MCP client library
│   ├── client.py
│   ├── tools.py
│   ├── tests/
│   └── README.md
│
├── observability/             # OpenTelemetry instrumentation
│   ├── tracing.py
│   ├── metrics.py
│   ├── logging.py
│   └── README.md
│
└── common/                    # Common utilities
    ├── config.py             # Configuration management
    ├── database.py           # Database utilities
    ├── kafka.py              # Kafka utilities
    └── types.py              # Common type definitions
```

### `/portal` - User Interfaces

```
portal/
├── backstage/                 # Main portal (React/Node.js)
│   ├── packages/
│   │   ├── app/              # Main app
│   │   └── backend/          # Backend
│   ├── plugins/              # Custom plugins
│   │   ├── data-products/    # Data product catalog
│   │   ├── ai-suggestions/   # AI suggestion UI
│   │   ├── governance/       # Governance dashboard
│   │   └── agents/           # Agent management
│   ├── app-config.yaml
│   ├── package.json
│   └── README.md
│
└── streamlit/                 # Internal tools (Python)
    ├── pages/
    │   ├── 1_Agent_Testing.py
    │   ├── 2_RAG_Query.py
    │   └── 3_Stream_Preview.py
    ├── app.py                # Main app
    ├── requirements.txt
    └── README.md
```

### `/infrastructure` - Infrastructure as Code

```
infrastructure/
├── terraform/                 # Terraform configurations
│   ├── modules/
│   │   ├── gke/             # GKE cluster
│   │   ├── cloud-run/       # Cloud Run services
│   │   ├── kafka/           # Confluent Cloud
│   │   └── networking/      # VPC, subnets
│   ├── environments/
│   │   ├── dev.tfvars
│   │   ├── staging.tfvars
│   │   └── production.tfvars
│   ├── main.tf
│   ├── variables.tf
│   └── outputs.tf
│
├── kubernetes/                # Kubernetes manifests
│   ├── base/                 # Base configs
│   ├── overlays/
│   │   ├── dev/
│   │   ├── staging/
│   │   └── production/
│   └── helm/                 # Helm charts
│
└── docker/                    # Docker configs
    ├── postgres/
    │   └── init.sql
    ├── prometheus/
    │   └── prometheus.yml
    └── grafana/
        ├── dashboards/
        └── datasources/
```

### `/docs` - Documentation

```
docs/
├── architecture/              # Architecture documentation
│   ├── overview.md
│   ├── services.md
│   ├── agents.md
│   └── data-flow.md
│
├── protocols/                 # Protocol specifications
│   ├── a2a-spec.md
│   ├── mcp-integration.md
│   └── openlineage.md
│
├── services/                  # Service documentation
│   ├── product-service.md
│   ├── agent-orchestration.md
│   └── ...
│
├── agents/                    # Agent documentation
│   ├── development-guide.md
│   ├── stream-analysis.md
│   └── ...
│
├── deployment/                # Deployment guides
│   ├── README.md
│   ├── gcp.md
│   ├── aws.md
│   └── azure.md
│
└── mkdocs.yml                # Documentation site config
```

### `/scripts` - Automation Scripts

```
scripts/
├── init-dev.sh               # Initialize dev environment
├── build-all.sh              # Build all services
├── deploy.sh                 # Deploy to environment
├── deploy-service.sh         # Deploy specific service
├── deploy-agent.sh           # Deploy specific agent
├── test-unit.sh              # Run unit tests
├── test-integration.sh       # Run integration tests
├── test-e2e.sh               # Run E2E tests
├── coverage.sh               # Generate coverage
├── lint.sh                   # Run linters
├── format.sh                 # Format code
├── create-service.sh         # Create new service
├── create-agent.sh           # Create new agent
├── generate-openapi.sh       # Generate OpenAPI specs
├── db-reset.sh               # Reset database
└── check-deps.sh             # Check dependencies
```

### `/tests` - Integration Tests

```
tests/
├── unit/                      # Unit tests (per service)
├── integration/               # Integration tests
│   ├── test_a2a_messaging.py
│   ├── test_product_lifecycle.py
│   └── test_agent_workflow.py
└── e2e/                       # End-to-end tests
    ├── test_product_suggestion.py
    └── test_full_workflow.py
```

### `/config` - Configuration Files

```
config/
├── dev.yaml                   # Development config
├── staging.yaml               # Staging config
├── production.yaml            # Production config
└── example.yaml               # Example configuration
```

### Root Files

```
platform/
├── README.md                  # Project overview
├── Makefile                   # Build automation
├── docker-compose.yml         # Local development
├── pyproject.toml             # Python dependencies
├── poetry.lock                # Locked dependencies
├── .gitignore                 # Git ignore rules
├── .pre-commit-config.yaml    # Pre-commit hooks
├── .github/                   # GitHub Actions
│   └── workflows/
│       ├── ci.yml
│       └── deploy.yml
├── VERSION                    # Version file
└── LICENSE                    # License file
```

---

## Service Structure Template

Each service follows this standard structure:

```
service-name/
├── src/
│   ├── api/                   # API routes
│   ├── models/                # Data models
│   ├── schemas/               # Request/response schemas
│   ├── services/              # Business logic
│   ├── config.py              # Configuration
│   └── main.py                # Entry point
├── tests/
│   ├── test_api.py
│   ├── test_services.py
│   └── conftest.py
├── alembic/                   # (if using database)
├── Dockerfile
├── pyproject.toml
├── .dockerignore
└── README.md
```

## Agent Structure Template

Each agent follows this standard structure:

```
agent-name/
├── src/
│   ├── handlers/              # Intent handlers
│   ├── processors/            # Data processors
│   ├── config.py              # Configuration
│   └── main.py                # Entry point (inherits BaseAgent)
├── tests/
│   ├── test_handlers.py
│   └── conftest.py
├── Dockerfile
├── pyproject.toml
└── README.md
```

---

## Key Principles

1. **Separation of Concerns**: Services, agents, and shared code are clearly separated
2. **Consistency**: All services/agents follow the same structure
3. **Testability**: Tests alongside code, integration tests separate
4. **Documentation**: Every component has README
5. **Configuration**: Environment-specific configs in `/config`
6. **Infrastructure as Code**: All infrastructure in `/infrastructure`
7. **Observability**: OpenTelemetry in all services
8. **Modularity**: Shared code in `/shared` for reuse

---

## Getting Started

1. Clone repository
2. Run `./scripts/init-dev.sh`
3. Edit `.env` file
4. Run `make docker-up`
5. Start developing!

See main [README.md](../README.md) for more details.
