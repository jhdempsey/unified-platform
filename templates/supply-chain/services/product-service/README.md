# Product Service

REST API for managing data products in the intelligent platform.

## 🚀 Quick Start

### **Install Dependencies**

```bash
pip install fastapi uvicorn sqlalchemy psycopg2-binary confluent-kafka
```

### **Set Environment Variables**

```bash
export DATABASE_URL="postgresql://platform:platform_dev@localhost:5432/platform"
export KAFKA_BOOTSTRAP_SERVERS="localhost:19093"
export SCHEMA_REGISTRY_URL="http://localhost:18081"
```

### **Run the Service**

```bash
python main.py
```

The API will be available at:
- **API**: http://localhost:8001
- **Docs**: http://localhost:8001/docs
- **Health**: http://localhost:8001/health

---

## 📋 API Endpoints

### **Products**

```bash
# Create product
curl -X POST http://localhost:8001/products \
  -H "Content-Type: application/json" \
  -d '{
    "product_name": "Supplier Master Data",
    "product_type": "DATASET",
    "owner": "data-team",
    "description": "Master data for all suppliers",
    "kafka_topic": "supplier-events",
    "tags": ["supplier", "master-data"],
    "created_by": "admin"
  }'

# List products
curl http://localhost:8001/products

# Get specific product
curl http://localhost:8001/products/PROD-ABC123

# Update product
curl -X PUT http://localhost:8001/products/PROD-ABC123 \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Updated description",
    "updated_by": "admin"
  }'

# Delete product
curl -X DELETE http://localhost:8001/products/PROD-ABC123
```

### **Statistics**

```bash
# Get product statistics
curl http://localhost:8001/stats
```

---

## 🗄️ Database Schema

### **data_products Table**

| Column | Type | Description |
|--------|------|-------------|
| product_id | VARCHAR(50) | Primary key |
| product_name | VARCHAR(200) | Product name |
| product_type | ENUM | DATASET, STREAM, API, REPORT, ML_MODEL |
| owner | VARCHAR(100) | Team or user owning the product |
| description | VARCHAR(1000) | Product description |
| schema_version | VARCHAR(20) | Schema version (semver) |
| schema_definition | JSON | Schema definition |
| tags | JSON | Array of tags |
| quality_score | FLOAT | Quality score (0-100) |
| kafka_topic | VARCHAR(200) | Associated Kafka topic |
| created_at | TIMESTAMP | Creation timestamp |
| updated_at | TIMESTAMP | Last update timestamp |
| created_by | VARCHAR(100) | Creator |
| updated_by | VARCHAR(100) | Last updater |
| metadata | JSON | Additional metadata |

---

## 📤 Kafka Integration

When products are created or updated, events are published to the `product-events` topic with Avro schema:

```json
{
  "event_id": "uuid",
  "product_id": "PROD-ABC123",
  "product_name": "Supplier Master Data",
  "product_type": "DATASET",
  "owner": "data-team",
  "kafka_topic": "supplier-events",
  "timestamp": 1234567890,
  "created_by": "admin"
}
```

---

## 🧪 Testing

```bash
# Health check
curl http://localhost:8001/health

# Create test product
curl -X POST http://localhost:8001/products \
  -H "Content-Type: application/json" \
  -d '{
    "product_name": "Test Product",
    "product_type": "STREAM",
    "owner": "test-team",
    "created_by": "tester"
  }'

# Check it was created
curl http://localhost:8001/products
```

---

## 📊 Architecture

```
Client Request
     ↓
FastAPI (main.py)
     ↓
CRUD Operations (crud.py)
     ↓
Database (PostgreSQL)
     ↓
Kafka Producer (kafka_producer.py)
     ↓
Kafka Topic (product-events)
```

---

## 🔧 Configuration

Environment variables:

- `DATABASE_URL` - PostgreSQL connection string
- `KAFKA_BOOTSTRAP_SERVERS` - Kafka brokers
- `SCHEMA_REGISTRY_URL` - Schema Registry URL
- `PORT` - Service port (default: 8001)

---

## 📚 Files

- `main.py` - FastAPI application
- `models.py` - SQLAlchemy database models
- `schemas.py` - Pydantic validation schemas
- `crud.py` - CRUD operations
- `database.py` - Database configuration
- `kafka_producer.py` - Kafka event producer

---

## 🎯 Next Steps

1. Start the service: `python main.py`
2. Open API docs: http://localhost:8001/docs
3. Create some products via the API
4. Check that events are in Kafka: `kafka-console-consumer --topic product-events --bootstrap-server localhost:19093`
5. Start the Stream Analysis Agent to monitor your products
