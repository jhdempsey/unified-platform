# Complete Platform Setup & Demo Guide

## 🎯 What You Built

You now have a complete **Intelligent Data Product Platform** with:

1. ✅ **Product Service** - REST API for data products
2. ✅ **Stream Analysis Agent** - AI-powered quality monitoring
3. ✅ **Kafka + Avro** - Event streaming with schema validation
4. ✅ **PostgreSQL** - Relational database
5. ✅ **Schema Registry** - Schema versioning and validation

---

## 🚀 Complete Setup (First Time)

### **Step 1: Copy Services to Your Project** (5 min)

```bash
cd ~/Work/AI_Development/platform-monorepo

# Copy Product Service
cp -r ~/Downloads/platform-services/product-service services/

# Copy Stream Analysis Agent
cp -r ~/Downloads/platform-services/stream-analysis-agent agents/
```

### **Step 2: Install Dependencies** (2 min)

```bash
# Install Python packages
pip install fastapi uvicorn sqlalchemy psycopg2-binary confluent-kafka anthropic pydantic

# Or if using pipenv
pipenv install fastapi uvicorn sqlalchemy psycopg2-binary confluent-kafka anthropic pydantic
```

### **Step 3: Set Environment Variables** (1 min)

```bash
# Add to your .env file
cat >> .env << 'EOF'

# Product Service
DATABASE_URL=postgresql://platform:platform_dev@localhost:5432/platform
KAFKA_BOOTSTRAP_SERVERS=localhost:19093
SCHEMA_REGISTRY_URL=http://localhost:18081

# Stream Analysis Agent  
ANTHROPIC_API_KEY=your-api-key-here

EOF
```

### **Step 4: Start Infrastructure** (1 min)

```bash
# Make sure Docker containers are running
docker-compose ps

# Should see: kafka, postgres, schema-registry, etc. all UP
```

---

## 🎬 Demo Flow (15 minutes)

### **Terminal 1: Start Product Service**

```bash
cd ~/Work/AI_Development/platform-monorepo/services/product-service
python main.py
```

**Expected output:**
```
🚀 Starting Product Service...
✅ Database tables created
✅ Product Service ready
INFO:     Uvicorn running on http://0.0.0.0:8001
📖 API docs: http://localhost:8001/docs
```

### **Terminal 2: Start Stream Analysis Agent**

```bash
cd ~/Work/AI_Development/platform-monorepo/agents/stream-analysis-agent
python main.py
```

**Expected output:**
```
🤖 Initializing Stream Analysis Agent...
✅ Agent initialized

🚀 STREAM ANALYSIS AGENT STARTING
📥 Monitoring topics: supplier-events, order-events, product-events
🤖 AI Analysis: Enabled

Press Ctrl+C to stop
```

### **Terminal 3: Use the Platform**

#### **1. Create Data Products**

```bash
# Create a supplier data product
curl -X POST http://localhost:8001/products \
  -H "Content-Type: application/json" \
  -d '{
    "product_name": "Supplier Master Data",
    "product_type": "DATASET",
    "owner": "data-team",
    "description": "Centralized supplier information",
    "kafka_topic": "supplier-events",
    "tags": ["supplier", "master-data", "core"],
    "quality_score": 95.5,
    "created_by": "admin"
  }'

# Create an order data product
curl -X POST http://localhost:8001/products \
  -H "Content-Type: application/json" \
  -d '{
    "product_name": "Order Stream",
    "product_type": "STREAM",
    "owner": "supply-chain-team",
    "description": "Real-time order events",
    "kafka_topic": "order-events",
    "tags": ["orders", "real-time", "supply-chain"],
    "quality_score": 88.0,
    "created_by": "admin"
  }'

# List all products
curl http://localhost:8001/products | jq
```

#### **2. Generate Test Data**

```bash
# Run test script to generate events
cd ~/Work/AI_Development/platform-monorepo
python scripts/test-kafka-avro.py
```

**Watch Terminal 2** - You'll see the agent analyzing the events!

```
📊 Analyzing batch from supplier-events: 3 messages
   Quality Score: 95.0
   Severity: LOW
   Issues: 0
   ✅ No alert needed

📊 Analyzing batch from order-events: 2 messages
   Quality Score: 100.0
   Severity: LOW
   Issues: 0
   ✅ No alert needed
```

#### **3. View Quality Alerts**

```bash
# Consume quality alerts
python << 'EOF'
import sys
sys.path.append('scripts')
from avro_consumer import AvroConsumerHelper

consumer = AvroConsumerHelper(group_id="demo-viewer")
consumer.subscribe(["quality-alerts"])

print("\n🚨 Monitoring Quality Alerts (Ctrl+C to stop)...\n")

for key, value, topic, partition, offset in consumer.consume(timeout=2.0):
    print(f"Alert #{offset + 1}")
    print(f"  Severity: {value['severity']}")
    print(f"  Topic: {value['topic_name']}")
    print(f"  Quality Score: {value['metrics']['quality_score']:.1f}")
    print(f"  Description: {value['description']}")
    print(f"  AI Analysis: {value['ai_analysis']}")
    print("-" * 70)
EOF
```

#### **4. Explore API**

Open browser: http://localhost:8001/docs

Try the interactive API:
- Create products
- Search products
- View statistics
- Update products

---

## 📊 Architecture Demo Points

### **For Interview Discussion:**

1. **Event-Driven Architecture**
   - Product Service produces events
   - Agent consumes and analyzes
   - Decoupled microservices

2. **Schema Evolution**
   - Avro schemas with Schema Registry
   - Backward compatibility
   - Type safety across services

3. **AI Integration**
   - Claude API for intelligent analysis
   - Real-time quality monitoring
   - Automated recommendations

4. **Data Quality**
   - Automated quality checks
   - Severity-based alerting
   - Metrics and scoring

5. **Scalability**
   - Kafka partitioning
   - Consumer groups
   - Horizontal scaling ready

---

## 🎨 Customization Ideas

### **Add More Product Types**

Edit `services/product-service/models.py`:

```python
class ProductType(enum.Enum):
    DATASET = "DATASET"
    STREAM = "STREAM"
    API = "API"
    REPORT = "REPORT"
    ML_MODEL = "ML_MODEL"
    DASHBOARD = "DASHBOARD"  # Add this
```

### **Enhance AI Analysis**

Edit `agents/stream-analysis-agent/analyzer.py`:

```python
# Add custom analysis logic
def analyze_supplier_data(self, messages):
    # Check for FDA certifications
    # Validate contact emails
    # Detect suspicious patterns
    pass
```

### **Add More Topics**

Edit `agents/stream-analysis-agent/main.py`:

```python
self.topics = [
    "supplier-events",
    "order-events",
    "product-events",
    "shipment-events",  # Add this
    "invoice-events"    # Add this
]
```

---

## 🔧 Troubleshooting

### **Product Service Won't Start**

```bash
# Check database connection
psql postgresql://platform:platform_dev@localhost:5432/platform

# Check Kafka
kafka-topics --list --bootstrap-server localhost:19093
```

### **Agent Not Receiving Messages**

```bash
# Check topics exist
kafka-topics --list --bootstrap-server localhost:19093

# Check messages in topic
kafka-console-consumer --topic supplier-events \
  --bootstrap-server localhost:19093 --from-beginning
```

### **No Alerts Being Produced**

```bash
# Check agent is running
ps aux | grep python

# Check alert topic
kafka-console-consumer --topic quality-alerts \
  --bootstrap-server localhost:19093 --from-beginning
```

---

## 🎯 Demo Script

**5-Minute Demo:**

1. Show Product Service API (http://localhost:8001/docs)
2. Create a product via API
3. Show event in Kafka topic
4. Show agent analyzing the event
5. Show quality alert if triggered

**15-Minute Deep Dive:**

1. Architecture overview
2. Create multiple products
3. Generate test data
4. Show real-time analysis
5. Demonstrate AI recommendations
6. Show schema evolution
7. Discuss scaling strategies

---

## 📚 Next Steps

1. ✅ **Both services running**
2. ✅ **Creating products via API**
3. ✅ **Agent analyzing events**
4. ⏭️ Add a frontend dashboard
5. ⏭️ Integrate with Grafana for metrics
6. ⏭️ Deploy to GCP (Kubernetes)
7. ⏭️ Add authentication & authorization

---

## 🎉 You're Ready!

You now have a complete, working platform demonstrating:

- Event-driven architecture
- AI-powered data quality
- Microservices
- Schema management
- Real-time processing

**Perfect for your iTradeNetwork interview!** 🚀
