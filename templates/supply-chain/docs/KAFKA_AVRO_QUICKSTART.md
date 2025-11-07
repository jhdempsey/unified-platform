# Kafka + Avro Setup - Quick Start

## 🚀 Get Started in 3 Steps

### **Step 1: Create Topics & Register Schemas (2 minutes)**

```bash
cd platform-monorepo
pipenv shell

# Create topics with Avro schemas
python scripts/create-kafka-topics.py
```

**Expected Output:**
```
🚀 Kafka Topic & Schema Registry Setup
=======================================

🔌 Connecting to Kafka and Schema Registry...
  ✅ Kafka: localhost:19093
  ✅ Schema Registry: http://localhost:18081

🔧 Creating Kafka topics...
  ➕ Creating topic 'supplier-events' (3 partitions)
  ✅ Topic 'supplier-events' created successfully
  ➕ Creating topic 'order-events' (3 partitions)
  ✅ Topic 'order-events' created successfully
  ...

📋 Registering Avro schemas...
  ✅ Registered schema for 'supplier-events-value' (ID: 1)
  ✅ Registered schema for 'order-events-value' (ID: 2)
  ...

✅ Setup complete!
```

---

### **Step 2: Test the Setup (1 minute)**

```bash
# Run comprehensive test
python scripts/test-kafka-avro.py
```

**What it does:**
- Produces test messages to all 5 topics
- Consumes and validates messages
- Verifies schema serialization/deserialization
- Shows you everything working end-to-end

**Expected Output:**
```
🧪 KAFKA + AVRO + SCHEMA REGISTRY TEST
=======================================

📤 PRODUCING TEST MESSAGES
1️⃣  Producing supplier events...
  ✅ Message delivered to supplier-events [0] @ 0
  ✅ Message delivered to supplier-events [1] @ 0
  ...

📥 CONSUMING TEST MESSAGES
📨 Message #1
   Topic: supplier-events
   Supplier: Test Supplier SUP-A1B2C3 (SUP-A1B2C3)
   Event: CREATED
   ...

✅ TEST COMPLETE!
🎉 Your Kafka + Avro setup is working perfectly!
```

---

### **Step 3: Use in Your Code**

#### **Producing Messages:**

```python
from scripts.avro_producer import AvroProducerHelper
import uuid
from datetime import datetime

# Initialize
producer = AvroProducerHelper()

# Create event matching Avro schema
supplier_event = {
    "event_id": str(uuid.uuid4()),
    "event_type": "CREATED",
    "supplier_id": "SUP-001",
    "supplier_name": "Fresh Produce Co",
    "supplier_code": "FPC",
    "country": "USA",
    "certification_status": "FDA Certified",
    "contact_email": "contact@freshproduce.com",
    "timestamp": int(datetime.now().timestamp() * 1000),
    "metadata": {"source": "api"}
}

# Produce (automatic schema validation!)
producer.produce(
    topic="supplier-events",
    value=supplier_event,
    schema_file="supplier-event.avsc",
    key="SUP-001"
)

producer.close()
```

#### **Consuming Messages:**

```python
from scripts.avro_consumer import AvroConsumerHelper

# Initialize
consumer = AvroConsumerHelper(
    group_id="my-app",
    auto_offset_reset="earliest"
)

# Subscribe
consumer.subscribe(["supplier-events", "order-events"])

# Consume (automatic deserialization!)
for key, value, topic, partition, offset in consumer.consume():
    print(f"Received: {value['supplier_name']}")
    # value is already a dict!
    
consumer.close()
```

---

## 📊 What You Have Now

### **5 Kafka Topics with Avro Schemas:**

1. **supplier-events** - Supplier lifecycle events
2. **order-events** - Order tracking events
3. **product-events** - Data product creation
4. **quality-alerts** - AI-generated quality alerts
5. **lineage-events** - Data lineage tracking

### **Benefits:**

- ✅ **Type Safety** - Schema validation at produce/consume
- ✅ **Schema Evolution** - Add fields without breaking consumers
- ✅ **Documentation** - Self-documenting data contracts
- ✅ **Compatibility** - Backward/forward compatibility
- ✅ **Versioning** - Track schema changes over time
- ✅ **Binary Format** - Compact, efficient Avro serialization

---

## 🔍 Verify Everything

### **Check Topics Exist:**

```bash
kafka-topics --list --bootstrap-server localhost:19093
```

### **Check Schemas Registered:**

```bash
curl http://localhost:18081/subjects
```

### **View Schema Details:**

```bash
curl http://localhost:18081/subjects/supplier-events-value/versions/latest | jq
```

---

## 🎯 Next Steps

Now that Kafka + Avro is working:

1. **Build Product Service** - REST API that produces product-events
2. **Build Stream Analysis Agent** - Consumes events, generates quality-alerts
3. **Add Data Quality Monitoring** - Real-time quality checks
4. **Build Lineage Tracking** - Automatic lineage-events generation

---

## 🆘 Troubleshooting

### **"Connection refused" errors**

```bash
# Check Docker containers are running
docker-compose ps

# Should see: kafka, schema-registry, zookeeper all UP
```

### **"Schema not found" errors**

```bash
# Re-run setup
python scripts/create-kafka-topics.py
```

### **Import errors**

```bash
# Install dependencies
pipenv install confluent-kafka fastavro
```

---

## 📚 Learn More

- **Avro Schemas:** `schemas/avro/README.md`
- **Producer Helper:** `scripts/avro_producer.py`
- **Consumer Helper:** `scripts/avro_consumer.py`
- **Test Script:** `scripts/test-kafka-avro.py`

---

**🎉 You're ready to build the platform!**
