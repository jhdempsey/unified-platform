# Docker Compose Configuration Guide

## 📦 Two Versions Available

### `docker-compose.yml` - Infrastructure Only (Recommended to Start)

**What it includes:**
- ✅ PostgreSQL (with initialized schema)
- ✅ Redis (A2A message bus)
- ✅ Redpanda/Kafka (streaming)
- ✅ Elasticsearch (catalog search)
- ✅ Jaeger (distributed tracing)
- ✅ Prometheus (metrics)
- ✅ Grafana (dashboards)

**What it DOESN'T include:**
- ❌ Application services (need implementation)
- ❌ Agents (need Dockerfiles)
- ❌ Portal/UI (need implementation)

**Use this when:**
- 🚀 Getting started
- 🔨 Developing first service
- ✅ Testing infrastructure
- 📊 Need a clean, working environment

**Start it:**
```bash
docker-compose up -d
```

---

### `docker-compose.full.yml` - Complete Stack (Aspirational)

**What it includes:**
- ✅ All infrastructure (same as above)
- 📝 All services (COMMENTED OUT - need implementation)
- 📝 All agents (COMMENTED OUT - need Dockerfiles)
- 📝 Portal/UI (COMMENTED OUT - need implementation)

**Use this as:**
- 📋 A reference for the full architecture
- 🎯 A roadmap for what to build
- 🔧 Incrementally uncomment as you implement

**How to use:**
```bash
# Start with just infrastructure
docker-compose -f docker-compose.full.yml up -d

# As you implement services, uncomment them in the file
# Then restart:
docker-compose -f docker-compose.full.yml up -d --build
```

---

## 🛠️ Implementation Workflow

### Phase 1: Infrastructure (NOW)
```bash
# Use docker-compose.yml
docker-compose up -d

# Verify all running
docker-compose ps
```

**Result:** 7 infrastructure services running ✅

---

### Phase 2: First Service (Week 1-2)

**Example: Product Service**

1. **Implement the service:**
```bash
cd services/product-service

# Create Dockerfile
cat > Dockerfile << 'EOF'
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY pyproject.toml poetry.lock* ./
RUN pip install poetry && poetry config virtualenvs.create false && poetry install --no-dev

# Copy code
COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
EOF

# Create pyproject.toml with dependencies
poetry init
poetry add fastapi uvicorn sqlalchemy asyncpg redis
```

2. **Add to docker-compose.yml:**
```yaml
  product-service:
    build:
      context: ./services/product-service
      dockerfile: Dockerfile
    container_name: platform-product-service
    ports:
      - "8001:8001"
    environment:
      DATABASE_URL: postgresql://platform:platform_dev@postgres:5432/platform
      REDIS_URL: redis://redis:6379/0
    depends_on:
      postgres:
        condition: service_healthy
    networks:
      - platform-network
    volumes:
      - ./services/product-service:/app
```

3. **Start everything:**
```bash
docker-compose up -d --build
```

**Result:** Infrastructure + Product Service ✅

---

### Phase 3: Add Agents (Week 3-4)

**Example: Stream Analysis Agent**

1. **Create Dockerfile:**
```bash
cd agents/stream-analysis

cat > Dockerfile << 'EOF'
FROM python:3.11-slim

WORKDIR /app

# Copy shared libraries
COPY ../../shared /app/shared

# Install dependencies
COPY pyproject.toml poetry.lock* ./
RUN pip install poetry && poetry config virtualenvs.create false && poetry install --no-dev

# Copy agent code
COPY . .

CMD ["python", "main.py"]
EOF

# Create dependencies
poetry init
poetry add redis opentelemetry-api
```

2. **Add to docker-compose.yml:**
```yaml
  agent-stream-analysis:
    build:
      context: ./agents/stream-analysis
      dockerfile: Dockerfile
    container_name: platform-agent-stream-analysis
    environment:
      REDIS_URL: redis://redis:6379/0
      MCP_SERVER_URL: http://mcp-server:8000
    depends_on:
      redis:
        condition: service_healthy
    networks:
      - platform-network
```

**Result:** Infrastructure + Services + Agents ✅

---

### Phase 4: Portal (Week 5-6)

Follow same pattern for Backstage and Streamlit.

---

## 🎯 Recommended Approach

### Option A: Start Minimal (Recommended)
```bash
# 1. Start with infrastructure only
docker-compose up -d

# 2. Develop services locally (outside Docker) first
cd services/product-service
poetry install
poetry run uvicorn main:app --reload

# 3. Once working, containerize and add to docker-compose
# 4. Repeat for each service/agent
```

**Advantages:**
- ✅ Faster iteration (no Docker rebuilds)
- ✅ Easier debugging
- ✅ Clear separation of concerns
- ✅ Can use your existing MCP server

---

### Option B: Build in Docker from Start
```bash
# 1. Use docker-compose.full.yml as template
# 2. Uncomment one service at a time
# 3. Implement, test, move to next
```

**Advantages:**
- ✅ Production-like environment
- ✅ Tests deployment issues early
- ✅ Consistent environments

**Disadvantages:**
- ⚠️ Slower iteration
- ⚠️ More complex debugging

---

## 💡 Pro Tips

### Hybrid Approach (Best of Both)
```bash
# Run infrastructure in Docker
docker-compose up -d postgres redis redpanda elasticsearch

# Run your service locally for development
cd services/product-service
export DATABASE_URL=postgresql://platform:platform_dev@localhost:5432/platform
export REDIS_URL=redis://localhost:6379/0
poetry run uvicorn main:app --reload

# When ready, containerize
docker-compose up -d product-service
```

---

### Selective Service Startup
```bash
# Start only specific services
docker-compose up -d postgres redis

# Add more as needed
docker-compose up -d redpanda elasticsearch

# Check what's running
docker-compose ps
```

---

### Integrate Your Existing MCP Server
```bash
# If you already have an MCP server running elsewhere:

# 1. Don't start it in Docker
# 2. Point agents to your existing server:
export MCP_SERVER_URL=http://localhost:8000  # Your existing server

# 3. Or add it to .env:
echo "MCP_SERVER_URL=http://host.docker.internal:8000" >> .env
```

---

## 📋 Summary

| File | Purpose | Use When |
|------|---------|----------|
| `docker-compose.yml` | Infrastructure only | Starting out, clean environment |
| `docker-compose.full.yml` | Complete stack reference | Planning, understanding architecture |

**Recommended path:**
1. Start with `docker-compose.yml` ✅
2. Reference `docker-compose.full.yml` for architecture 📋
3. Implement services one by one 🔨
4. Add to `docker-compose.yml` incrementally ➕
5. Eventually, `docker-compose.yml` becomes your full stack 🎉

---

## 🆘 Need Help?

**Can't decide?**
- Use `docker-compose.yml` (infrastructure only)
- Develop services locally first
- Containerize when stable

**Want to see the vision?**
- Look at `docker-compose.full.yml`
- See all services with TODO comments
- Implement incrementally

**Have your own MCP server?**
- Use infrastructure only
- Point to your existing server
- Skip the MCP server section
