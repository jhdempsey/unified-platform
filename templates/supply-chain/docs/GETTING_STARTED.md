# Getting Started with the Platform

This guide will help you set up your local development environment and start contributing to the Intelligent Data Product Platform.

## Prerequisites

Before you begin, ensure you have the following installed:

- **Docker** (20.10+) and **Docker Compose** (2.0+)
- **Python** 3.11 or higher
- **Node.js** 18+ and **npm** or **yarn**
- **Poetry** (Python dependency management)
- **Git**
- **kubectl** (for Kubernetes operations)
- **Terraform** 1.5+ (for infrastructure)

### Optional but Recommended
- **VS Code** with Python, Docker, and YAML extensions
- **Postman** or **Insomnia** for API testing
- **pre-commit** for git hooks

---

## Quick Start (5 minutes)

```bash
# 1. Clone the repository
git clone <repository-url>
cd platform

# 2. Initialize development environment
./scripts/init-dev.sh

# 3. Edit environment variables
vi .env  # Add your API keys

# 4. Start all services
make docker-up

# 5. Verify services are running
make status
```

**That's it!** You now have a fully functional local platform.

---

## Access the Platform

Once everything is running, you can access:

| Service | URL | Credentials |
|---------|-----|-------------|
| **Backstage Portal** | http://localhost:3000 | - |
| **Streamlit Tools** | http://localhost:8501 | - |
| **Product Service API** | http://localhost:8001 | - |
| **MCP Server** | http://localhost:8000 | - |
| **Jaeger UI** | http://localhost:16686 | - |
| **Grafana** | http://localhost:3001 | admin/admin |
| **Prometheus** | http://localhost:9090 | - |

---

## Development Workflow

### 1. Create a Feature Branch

```bash
git checkout -b feature/my-new-feature
```

### 2. Make Changes

Edit code in:
- `services/` for backend services
- `agents/` for intelligent agents
- `portal/` for UI changes
- `infrastructure/` for infrastructure changes

### 3. Run Tests

```bash
# Unit tests for specific service
cd services/product-service
poetry run pytest

# Or run all tests
make test
```

### 4. Format and Lint

```bash
# Format code
make format

# Run linters
make lint
```

### 5. Commit Changes

```bash
git add .
git commit -m "feat: add new data product suggestion logic"

# Pre-commit hooks will run automatically
```

### 6. Push and Create PR

```bash
git push origin feature/my-new-feature
# Create pull request on GitHub
```

---

## Common Development Tasks

### Adding a New Microservice

```bash
# Generate service boilerplate
make create-service NAME=my-service LANGUAGE=python

# Implement service
cd services/my-service
# ... edit files ...

# Add to docker-compose.yml
# Add to kubernetes manifests
# Update API gateway routes
```

### Creating a New Agent

```bash
# Generate agent boilerplate
make create-agent NAME=my-agent

# Implement agent
cd agents/my-agent
# Edit main.py, inherit from BaseAgent or ScheduledAgent

# Register intent handlers
# Implement execute() method

# Test locally
poetry run python main.py
```

### Working with Database

```bash
# Create migration
cd services/product-service
poetry run alembic revision --autogenerate -m "add new table"

# Apply migration
poetry run alembic upgrade head

# Rollback
poetry run alembic downgrade -1

# Reset database (WARNING: destroys data)
make db-reset
```

### Debugging

```bash
# View logs for specific service
docker-compose logs -f product-service

# Or in Kubernetes
kubectl logs -f deployment/product-service -n dev

# Shell into container
make shell-service SERVICE=product-service

# View traces in Jaeger
# Open http://localhost:16686
```

### Testing Agents

Use the Streamlit interface for testing:

1. Go to http://localhost:8501
2. Select "Agent Testing" page
3. Send test messages to agents
4. View A2A message flow
5. Inspect agent responses

---

## Project Structure Cheat Sheet

```
platform/
├── services/        # Backend microservices (FastAPI)
├── agents/          # Intelligent agents (Python + A2A)
├── shared/          # Shared libraries (A2A, MCP, observability)
├── portal/          # UIs (Backstage + Streamlit)
├── infrastructure/  # IaC (Terraform + K8s)
├── docs/            # Documentation (MkDocs)
├── scripts/         # Automation scripts
└── tests/           # Integration tests
```

See [DIRECTORY_STRUCTURE.md](./DIRECTORY_STRUCTURE.md) for full details.

---

## Understanding the Architecture

### Data Flow

```
User (Backstage) 
  → API Gateway
  → Product Service (CRUD)
  → Agent Orchestration (workflows)
  → Agents (A2A messages via Redis)
  → MCP Server (tools)
  → Data Platform (Kafka, Schema Registry, etc.)
```

### Agent Communication

Agents communicate via **A2A Protocol** over Redis Pub/Sub:

```python
# Agent A sends message to Agent B
message = A2AMessage(
    sender=A2AAgent(agent_id="agent-a"),
    recipient=A2AAgent(agent_id="agent-b"),
    intent="do_something",
    payload={"data": "value"}
)
await agent_a.send_message(message)

# Agent B receives and handles
@agent_b.register_intent_handler("do_something")
async def handle(message):
    # Process message
    return {"result": "done"}
```

### MCP Tool Calling

Agents call tools via **MCP Server**:

```python
result = await agent.call_mcp_tool(
    "analyze_kafka_streams",
    {"lookback_days": 7}
)
```

---

## Configuration

### Environment Variables

Edit `.env` file:

```bash
# Required
DATABASE_URL=postgresql://...
REDIS_URL=redis://...
KAFKA_BOOTSTRAP_SERVERS=...

# LLM API Keys (add yours)
GEMINI_API_KEY=your_key
ANTHROPIC_API_KEY=your_key
OPENAI_API_KEY=your_key

# Optional
LOG_LEVEL=INFO
ENVIRONMENT=development
```

### Service-Specific Config

Edit `config/dev.yaml`:

```yaml
services:
  product-service:
    max_results: 100
    cache_ttl: 300

agents:
  stream-analysis:
    schedule_interval: 300
    min_confidence: 0.7
```

---

## Troubleshooting

### Services Won't Start

```bash
# Check if ports are available
lsof -i :5432  # PostgreSQL
lsof -i :6379  # Redis
lsof -i :19092 # Kafka

# Check Docker resources
docker system df
docker system prune  # Free up space

# Restart everything
make docker-down
make docker-up
```

### Database Connection Issues

```bash
# Check PostgreSQL is running
docker-compose ps postgres

# Test connection
docker-compose exec postgres psql -U platform -d platform

# Reset database
make db-reset
```

### Agent Not Receiving Messages

```bash
# Check Redis
docker-compose exec redis redis-cli ping

# View Redis pub/sub channels
docker-compose exec redis redis-cli PUBSUB CHANNELS

# Check agent logs
docker-compose logs -f agent-stream-analysis
```

### Import Errors

```bash
# Reinstall dependencies
poetry install

# Or rebuild container
docker-compose build service-name
docker-compose up -d service-name
```

---

## Best Practices

### Code Style

- Use **Black** for Python formatting (line length: 100)
- Use **Ruff** for linting
- Use **MyPy** for type checking
- Follow **PEP 8** naming conventions

### Git Commits

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add new feature
fix: fix bug
docs: update documentation
test: add tests
refactor: refactor code
chore: update dependencies
```

### Testing

- Write tests for all new features
- Aim for >80% code coverage
- Use pytest fixtures for setup
- Mock external dependencies

### Documentation

- Every service/agent has README.md
- Update docs/ when changing architecture
- Add docstrings to all public functions
- Include usage examples

---

## Next Steps

1. **Read the docs**: Check `docs/architecture/` for system design
2. **Explore services**: Look at `services/` to understand APIs
3. **Try agents**: Run Stream Analysis Agent and see it work
4. **Create something**: Build a new agent or tool
5. **Ask questions**: Open issues or join discussions

---

## Resources

- [Architecture Overview](./architecture/overview.md)
- [A2A Protocol Specification](./protocols/a2a-spec.md)
- [Agent Development Guide](./agents/development-guide.md)
- [Deployment Guide](./deployment/README.md)
- [API Documentation](http://localhost:8001/docs) (when running)

---

## Getting Help

- **Issues**: GitHub Issues
- **Discussions**: GitHub Discussions
- **Slack**: #platform-dev (internal)
- **Email**: platform-team@company.com

---

Happy coding! 🚀
