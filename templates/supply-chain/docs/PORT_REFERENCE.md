# Platform Services - Port Reference

## 🔌 **Port Configuration**

These ports have been adjusted to avoid conflicts with existing services on your machine.

---

## 📊 **Infrastructure Services**

| Service | Default Port | **Your Port** | Access URL | Purpose |
|---------|--------------|---------------|------------|---------|
| **PostgreSQL** | 5432 | **5432** | `localhost:5432` | Product metadata, lineage |
| **Redis** | 6379 | **6380** | `localhost:6380` | Caching, sessions |
| **ZooKeeper** | 2181 | **2181** | `localhost:2181` | Kafka coordination |
| **Kafka (Internal)** | 9092 | **9092** | `localhost:9092` | Container-to-container |
| **Kafka (External)** | 19092 | **19093** | `localhost:19093` | Host access |
| **Schema Registry** | 8081 | **18081** | `http://localhost:18081` | Avro schemas |
| **Elasticsearch** | 9200 | **9200** | `http://localhost:9200` | Logs, search |

---

## 🎯 **Application Services**

| Service | Port | Access URL | Status | Purpose |
|---------|------|------------|--------|---------|
| **Product Service** | **8001** | `http://localhost:8001` | ✅ Running | Product CRUD API |
| **Product Generator** | **8003** | `http://localhost:8003` | ✅ Running | AI product creation |
| **Discovery & Catalog** | **8004** | `http://localhost:8004` | ✅ Running | Topic discovery, intelligence |
| **Stream Analysis Agent** | N/A | Background | ✅ Running | Quality monitoring |

---

## 📈 **Monitoring & Observability**

| Service | Default Port | **Your Port** | Access URL | Credentials |
|---------|--------------|---------------|------------|-------------|
| **Prometheus** | 9090 | **9095** | `http://localhost:9095` | - |
| **Grafana** | 3000 | **3002** | `http://localhost:3002` | admin / admin |
| **Jaeger UI** | 16686 | **16686** | `http://localhost:16686` | - |
| **Jaeger OTLP gRPC** | 4317 | **4317** | `localhost:4317` | - |
| **Jaeger OTLP HTTP** | 4318 | **4318** | `http://localhost:4318` | - |

---

## 🎨 **Optional Services**

| Service | Port | Access URL | Purpose |
|---------|------|------------|---------|
| **Confluent Control Center** | **9021** | `http://localhost:9021` | Kafka UI (optional) |
| **Streamlit Dashboard** | **8501** | `http://localhost:8501` | Data portal UI |
| **Backstage** | **7007** | `http://localhost:7007` | Developer portal |

---

## ⚙️ **Environment Variables**

Update your `.env` file with these values:

```bash
# Database
DATABASE_URL=postgresql://platform:platform_dev@localhost:5432/platform

# Redis (CUSTOM PORT)
REDIS_URL=redis://localhost:6380/0

# Kafka (CUSTOM PORT)
KAFKA_BOOTSTRAP_SERVERS=localhost:19093
SCHEMA_REGISTRY_URL=http://localhost:18081

# Elasticsearch
ELASTICSEARCH_URL=http://localhost:9200

# OpenTelemetry
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317

# AI
ANTHROPIC_API_KEY=your-key-here

# Service Ports
PRODUCT_SERVICE_PORT=8001
PRODUCT_GENERATOR_PORT=8003
DISCOVERY_AGENT_PORT=8004

# Application
LOG_LEVEL=INFO
ENVIRONMENT=development
```

---

## 🎯 **Confluent Stack**

Using **official Confluent Platform Docker images**:
- ✅ `confluentinc/cp-zookeeper:7.5.0`
- ✅ `confluentinc/cp-kafka:7.5.0`
- ✅ `confluentinc/cp-schema-registry:7.5.0`

**Why Confluent?** Official images provide better stability, enterprise features, and align with Confluent ecosystem best practices.

---

## 🚀 **Quick Start**

### **Start Infrastructure**
```bash
# Start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f kafka schema-registry
```

### **Start Application Services**

**Terminal 1: Product Service**
```bash
cd services/product-service
python main.py
# Starts on http://localhost:8001
```

**Terminal 2: Product Generator**
```bash
cd agents/product-generator-agent
python api.py
# Starts on http://localhost:8003
```

**Terminal 3: Discovery & Catalog**
```bash
cd agents/discovery-agent
python catalog_api.py
# Starts on http://localhost:8004
```

**Terminal 4: Stream Analysis**
```bash
cd agents/stream-analysis-agent
python main.py
# Background agent (no HTTP port)
```

---

## 🔍 **Verify Services**

### **Infrastructure**
```bash
# PostgreSQL
psql -h localhost -p 5432 -U platform -d platform

# Redis (CUSTOM PORT)
redis-cli -h localhost -p 6380 ping

# Kafka (use external port 19093)
kafka-topics --bootstrap-server localhost:19093 --list

# Schema Registry (CUSTOM PORT)
curl http://localhost:18081/subjects

# Elasticsearch
curl http://localhost:9200/_cluster/health
```

### **Application Services**
```bash
# Product Service
curl http://localhost:8001/health

# Product Generator
curl http://localhost:8003/health

# Discovery & Catalog
curl http://localhost:8004/health
```

### **Monitoring**
```bash
# Prometheus (CUSTOM PORT)
open http://localhost:9095

# Grafana (CUSTOM PORT)
open http://localhost:3002
# Login: admin / admin

# Jaeger
open http://localhost:16686
```

---

## 📊 **Kafka Quick Commands**

### **Using Docker Exec (Internal Port)**
```bash
# Create topic
docker-compose exec kafka kafka-topics \
  --bootstrap-server localhost:9092 \
  --create \
  --topic test-topic \
  --partitions 3 \
  --replication-factor 1

# List topics
docker-compose exec kafka kafka-topics \
  --bootstrap-server localhost:9092 \
  --list

# Describe topic
docker-compose exec kafka kafka-topics \
  --bootstrap-server localhost:9092 \
  --describe \
  --topic test-topic
```

### **Using Host Tools (External Port 19093)**
```bash
# Produce messages
kafka-console-producer \
  --bootstrap-server localhost:19093 \
  --topic test-topic

# Consume messages
kafka-console-consumer \
  --bootstrap-server localhost:19093 \
  --topic test-topic \
  --from-beginning
```

---

## 📋 **Schema Registry Commands**

```bash
# List all subjects
curl http://localhost:18081/subjects

# Get schema for subject
curl http://localhost:18081/subjects/supplier-events-value/versions/latest

# Register new schema
curl -X POST http://localhost:18081/subjects/test-value/versions \
  -H "Content-Type: application/vnd.schemaregistry.v1+json" \
  -d '{"schema": "{\"type\":\"record\",\"name\":\"Test\",\"fields\":[{\"name\":\"id\",\"type\":\"string\"}]}"}'

# Check compatibility
curl -X POST http://localhost:18081/compatibility/subjects/test-value/versions/latest \
  -H "Content-Type: application/vnd.schemaregistry.v1+json" \
  -d '{"schema": "..."}'
```

---

## 🎨 **Optional: Confluent Control Center**

Provides a full Kafka UI for monitoring and management.

### **Enable Control Center**
Uncomment the `control-center` section in `docker-compose.yml`:

```yaml
control-center:
  image: confluentinc/cp-enterprise-control-center:7.5.0
  ports:
    - "9021:9021"
  # ... (rest of config)
```

Then:
```bash
docker-compose up -d control-center
```

Access at: **http://localhost:9021**

Features:
- 📊 Cluster health monitoring
- 📈 Topic browser with message viewer
- 🔍 Consumer lag tracking
- ⚙️ Configuration management
- 🔌 Connector management

---

## 💡 **Why These Ports?**

### **Conflicts Avoided**
Your machine already had services on these ports:
- ❌ **6379** → Moved Redis to **6380**
- ❌ **9090** → Moved Prometheus to **9095**
- ❌ **19092** → Moved Kafka external to **19093**
- ❌ **3001** → Moved Grafana to **3002**

### **Port Ranges**
- **5000-5999**: Databases (PostgreSQL, Redis)
- **8000-8999**: Application services
- **9000-9999**: Infrastructure & monitoring
- **18000-18999**: Schema Registry (avoid conflicts)
- **19000-19999**: Kafka external access

---

## 🆘 **Troubleshooting**

### **Port Already in Use**
```bash
# Find what's using a port
lsof -i :8001

# Kill the process
kill -9 <PID>

# Or use fuser
fuser -k 8001/tcp
```

### **Kafka Won't Start**
```bash
# Check ZooKeeper is healthy
docker-compose logs zookeeper
docker-compose ps zookeeper

# Restart in order
docker-compose restart zookeeper
sleep 10
docker-compose restart kafka
```

### **Schema Registry Connection Issues**
```bash
# Ensure Kafka is healthy first
docker-compose exec kafka kafka-broker-api-versions \
  --bootstrap-server localhost:9092

# Check Schema Registry logs
docker-compose logs schema-registry

# Test connection
curl http://localhost:18081/subjects
```

### **Application Service Won't Start**
```bash
# Check if port is available
lsof -i :8001

# Check environment variables
cat .env

# Test database connection
psql -h localhost -p 5432 -U platform -d platform -c "SELECT 1"

# Test Kafka connection
kafka-topics --bootstrap-server localhost:19093 --list
```

### **Can't Connect from Host**
```bash
# Check Docker network
docker-compose ps

# Check KAFKA_ADVERTISED_LISTENERS in docker-compose.yml
# Should have: PLAINTEXT_HOST://localhost:19093

# Restart Kafka with clean state
docker-compose down
docker volume rm $(docker volume ls -q | grep kafka)
docker-compose up -d
```

---

## 📝 **Important Notes**

### **Container Communication**
- Containers use **internal ports** (e.g., Kafka on 9092)
- Host access uses **external ports** (e.g., Kafka on 19093)
- Schema Registry always uses **18081** (external)

### **Data Persistence**
All data persists in Docker volumes:
```bash
# List volumes
docker volume ls | grep platform

# Backup volume
docker run --rm -v platform_postgres_data:/data -v $(pwd):/backup \
  alpine tar czf /backup/postgres-backup.tar.gz -C /data .

# Remove all volumes (DANGER!)
docker-compose down -v
```

### **Health Checks**
All services include health checks. Check status:
```bash
docker-compose ps
# healthy = green checkmark
# unhealthy = red X
```

---

## 🔗 **API Documentation**

Interactive API docs (Swagger UI):

- **Product Service**: http://localhost:8001/docs
- **Product Generator**: http://localhost:8003/docs
- **Discovery & Catalog**: http://localhost:8004/docs

---

## 📚 **Related Documentation**

- [Getting Started Guide](GETTING_STARTED.md)
- [Docker Compose Guide](DOCKER_COMPOSE_GUIDE.md)
- [Kafka & Avro Quickstart](KAFKA_AVRO_QUICKSTART.md)
- [Complete Platform Guide](COMPLETE_PLATFORM_GUIDE.md)

---

## 🎉 **Quick Health Check**

Run this to verify everything is working:

```bash
#!/bin/bash
echo "🔍 Checking Platform Health..."
echo ""

# Infrastructure
echo "📊 Infrastructure:"
redis-cli -h localhost -p 6380 ping && echo "  ✅ Redis" || echo "  ❌ Redis"
curl -s http://localhost:18081/subjects > /dev/null && echo "  ✅ Schema Registry" || echo "  ❌ Schema Registry"
kafka-topics --bootstrap-server localhost:19093 --list > /dev/null 2>&1 && echo "  ✅ Kafka" || echo "  ❌ Kafka"
psql -h localhost -p 5432 -U platform -d platform -c "SELECT 1" > /dev/null 2>&1 && echo "  ✅ PostgreSQL" || echo "  ❌ PostgreSQL"

# Services
echo ""
echo "🎯 Application Services:"
curl -s http://localhost:8001/health > /dev/null && echo "  ✅ Product Service (8001)" || echo "  ❌ Product Service (8001)"
curl -s http://localhost:8003/health > /dev/null && echo "  ✅ Product Generator (8003)" || echo "  ❌ Product Generator (8003)"
curl -s http://localhost:8004/health > /dev/null && echo "  ✅ Discovery Agent (8004)" || echo "  ❌ Discovery Agent (8004)"

# Monitoring
echo ""
echo "📈 Monitoring:"
curl -s http://localhost:9095/-/healthy > /dev/null && echo "  ✅ Prometheus (9095)" || echo "  ❌ Prometheus (9095)"
curl -s http://localhost:3002/api/health > /dev/null && echo "  ✅ Grafana (3002)" || echo "  ❌ Grafana (3002)"

echo ""
echo "✅ Health check complete!"
```

Save as `scripts/health-check.sh` and run:
```bash
chmod +x scripts/health-check.sh
./scripts/health-check.sh
```

---

**Last Updated:** 2024-10-27  
**Platform Version:** 1.0.0
