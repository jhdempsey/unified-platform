# Avro Schemas

This directory contains Avro schemas for all platform events. Schemas are registered with the Confluent Schema Registry and enforce data contracts across the platform.

## 📋 Schema Files

### **supplier-event.avsc**
Events related to supplier lifecycle (creation, updates, verification)

**Topics:** `supplier-events`

**Key Fields:**
- `supplier_id` - Unique supplier identifier
- `event_type` - CREATED, UPDATED, DELETED, VERIFIED, SUSPENDED
- `supplier_name` - Name of supplier
- `certification_status` - FDA, HACCP, ISO certifications

**Use Cases:**
- Track supplier onboarding
- Monitor certification status
- Audit supplier changes

---

### **order-event.avsc**
Events tracking order lifecycle through supply chain

**Topics:** `order-events`

**Key Fields:**
- `order_id` - Unique order identifier
- `event_type` - PLACED, CONFIRMED, SHIPPED, DELIVERED, CANCELLED
- `items[]` - Array of order items
- `shipping_address` - Delivery location

**Use Cases:**
- Order tracking and monitoring
- Supply chain analytics
- Delivery performance metrics

---

### **product-created.avsc**
Events emitted when new data products are created

**Topics:** `product-events`

**Key Fields:**
- `product_id` - Unique data product ID
- `product_type` - DATASET, STREAM, API, REPORT, ML_MODEL
- `kafka_topic` - Associated Kafka topic (if stream)
- `quality_score` - Initial quality assessment

**Use Cases:**
- Data product catalog
- Product lifecycle tracking
- Quality monitoring

---

### **quality-alert.avsc**
AI-generated alerts for data quality issues

**Topics:** `quality-alerts`

**Key Fields:**
- `alert_type` - ANOMALY, MISSING_DATA, SCHEMA_VIOLATION, THRESHOLD_BREACH, DATA_DRIFT
- `severity` - LOW, MEDIUM, HIGH, CRITICAL
- `ai_analysis` - AI-generated recommendations
- `metrics` - Quality metrics (completeness, accuracy, etc.)

**Use Cases:**
- Automated quality monitoring
- Alert notification system
- Data governance dashboard

---

### **lineage-event.avsc**
Events capturing data lineage and transformations

**Topics:** `lineage-events`

**Key Fields:**
- `lineage_type` - INGESTION, TRANSFORMATION, AGGREGATION, EXPORT, DERIVATION
- `source_product_id` - Input data product
- `target_product_id` - Output data product
- `transformation_logic` - SQL or description of transformation

**Use Cases:**
- Data lineage tracking
- Impact analysis
- Compliance auditing

---

## 🚀 Usage

### **Creating Topics with Schemas**

```bash
# Run the setup script
python scripts/create-kafka-topics.py
```

This will:
1. Create all Kafka topics
2. Register schemas with Schema Registry
3. Verify setup

### **Producing Messages**

```python
from scripts.avro_producer import AvroProducerHelper
import uuid
from datetime import datetime

# Initialize producer
producer = AvroProducerHelper()

# Create event
event = {
    "event_id": str(uuid.uuid4()),
    "event_type": "CREATED",
    "supplier_id": "SUP-001",
    "supplier_name": "Fresh Produce Co",
    "supplier_code": "FPC",
    "country": "USA",
    "certification_status": "FDA Certified",
    "contact_email": "contact@freshproduce.com",
    "timestamp": int(datetime.now().timestamp() * 1000),
    "metadata": {}
}

# Produce (schema validation automatic)
producer.produce(
    topic="supplier-events",
    value=event,
    schema_file="supplier-event.avsc",
    key="SUP-001"
)

producer.close()
```

### **Consuming Messages**

```python
from scripts.avro_consumer import AvroConsumerHelper

# Initialize consumer
consumer = AvroConsumerHelper(
    group_id="my-consumer-group",
    auto_offset_reset="earliest"
)

# Subscribe
consumer.subscribe(["supplier-events"])

# Consume (automatic deserialization)
for key, value, topic, partition, offset in consumer.consume():
    print(f"Supplier: {value['supplier_name']}")
    print(f"Event: {value['event_type']}")
    
consumer.close()
```

---

## 📊 Schema Evolution

Schemas support evolution with backward/forward compatibility:

### **Adding Optional Fields** (Backward Compatible)

```json
{
  "name": "new_field",
  "type": ["null", "string"],
  "default": null
}
```

Old consumers can still read new messages.

### **Removing Fields** (Forward Compatible)

Remove field from schema definition. New consumers ignore unknown fields in old messages.

### **Changing Field Types** (Breaking Change)

Requires new schema version and topic migration.

---

## 🔍 Viewing Schemas

### **List All Schemas**

```bash
curl http://localhost:18081/subjects
```

### **Get Specific Schema**

```bash
curl http://localhost:18081/subjects/supplier-events-value/versions/latest
```

### **Get Schema Versions**

```bash
curl http://localhost:18081/subjects/supplier-events-value/versions
```

---

## ✅ Testing

### **Run Full Test Suite**

```bash
python scripts/test-kafka-avro.py
```

This will:
1. Produce test messages to all topics
2. Consume and validate messages
3. Verify schema registration
4. Test serialization/deserialization

### **Manual Testing**

```bash
# Produce a test message
python scripts/avro_producer.py

# Consume messages
python scripts/avro_consumer.py
```

---

## 📚 Schema Registry UI

View schemas visually at: http://localhost:9021 (Confluent Control Center)

Or use the REST API: http://localhost:18081

---

## 🎯 Best Practices

1. **Always use Schema Registry** - Enforces contracts
2. **Version schemas semantically** - Use semver (1.0.0 → 1.1.0 → 2.0.0)
3. **Maintain backward compatibility** - When possible
4. **Document schema changes** - In commit messages
5. **Test schema evolution** - Before deploying
6. **Use logical types** - For timestamps, decimals, etc.
7. **Add documentation** - In `doc` fields

---

## 🆘 Troubleshooting

### **Schema Registration Failed**

```bash
# Check Schema Registry is running
curl http://localhost:18081/subjects

# Check network connectivity
docker ps | grep schema-registry
```

### **Deserialization Error**

```bash
# Verify schema exists
curl http://localhost:18081/subjects/YOUR-TOPIC-value/versions/latest

# Check schema ID in message matches registry
```

### **Incompatible Schema Change**

```bash
# Test compatibility
curl -X POST -H "Content-Type: application/vnd.schemaregistry.v1+json" \
  --data @test-schema.json \
  http://localhost:18081/compatibility/subjects/YOUR-TOPIC-value/versions/latest
```

---

## 📖 Resources

- [Avro Specification](https://avro.apache.org/docs/current/spec.html)
- [Schema Registry API](https://docs.confluent.io/platform/current/schema-registry/develop/api.html)
- [Schema Evolution](https://docs.confluent.io/platform/current/schema-registry/avro.html)
- [Confluent Python Client](https://docs.confluent.io/kafka-clients/python/current/overview.html)
