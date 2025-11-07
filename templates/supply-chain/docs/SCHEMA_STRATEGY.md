# Schema Management Strategy

## 🎯 **Core Principle: Schema Registry First**

**ALL Kafka topics MUST use Avro serialization with schemas registered in Confluent Schema Registry.**

This ensures:
- ✅ **Type safety** - Producers and consumers agree on data structure
- ✅ **Schema evolution** - Backward/forward compatibility rules enforced
- ✅ **Documentation** - Schema serves as contract and documentation
- ✅ **Governance** - Centralized schema management and versioning
- ✅ **Data quality** - Invalid data rejected at serialization

---

## 📋 **Schema Registry Rules**

### **Rule 1: No Raw JSON**
❌ **Never send raw JSON to Kafka topics**
```python
# WRONG - Don't do this
producer.send('my-topic', value=json.dumps(data))
```

✅ **Always use Avro with Schema Registry**
```python
# CORRECT
from confluent_kafka import avro
from confluent_kafka.avro import AvroProducer

producer = AvroProducer({
    'bootstrap.servers': 'localhost:19093',
    'schema.registry.url': 'http://localhost:18081'
}, default_value_schema=avro_schema)

producer.produce(topic='my-topic', value=data)
```

### **Rule 2: Schema-First Development**
1. **Define schema** in Schema Registry
2. **Generate code** from schema (optional)
3. **Implement producer/consumer** using schema

### **Rule 3: Compatibility Modes**
- **Data products**: `FULL` or `BACKWARD` (consumers can read old data)
- **Events**: `FORWARD` (producers can send new formats)
- **Critical topics**: `FULL_TRANSITIVE` (all versions compatible)

---

## 🏗️ **Implementation Pattern**

### **1. Register Schema (via Agent or Manual)**

```python
from confluent_kafka.schema_registry import SchemaRegistryClient, Schema

schema_registry = SchemaRegistryClient({'url': 'http://localhost:18081'})

# Define Avro schema
supplier_reliability_schema = """
{
  "type": "record",
  "name": "SupplierReliabilityScore",
  "namespace": "com.platform.supplychain",
  "doc": "Real-time supplier reliability metrics",
  "fields": [
    {
      "name": "supplier_id",
      "type": "string",
      "doc": "Unique supplier identifier"
    },
    {
      "name": "window_end",
      "type": {
        "type": "long",
        "logicalType": "timestamp-millis"
      },
      "doc": "End of aggregation window"
    },
    {
      "name": "quality_acceptance_rate",
      "type": "double",
      "doc": "Percentage of quality checks passed"
    },
    {
      "name": "on_time_delivery_rate",
      "type": "double",
      "doc": "Percentage of on-time deliveries"
    },
    {
      "name": "reliability_score",
      "type": "double",
      "doc": "Composite reliability score (0-100)"
    },
    {
      "name": "delivery_count",
      "type": "long",
      "doc": "Number of deliveries in window"
    }
  ]
}
"""

# Register schema
schema = Schema(supplier_reliability_schema, schema_type="AVRO")
schema_id = schema_registry.register_schema(
    subject='supplier-reliability-score-value',
    schema=schema
)

print(f"Registered schema with ID: {schema_id}")
```

### **2. Produce with Avro**

```python
from confluent_kafka import avro
from confluent_kafka.avro import AvroProducer

# Create producer with Schema Registry
avro_producer = AvroProducer({
    'bootstrap.servers': 'localhost:19093',
    'schema.registry.url': 'http://localhost:18081'
}, default_value_schema=avro.loads(supplier_reliability_schema))

# Produce message
value = {
    'supplier_id': 'SUP-12345',
    'window_end': 1698336000000,
    'quality_acceptance_rate': 0.95,
    'on_time_delivery_rate': 0.88,
    'reliability_score': 91.5,
    'delivery_count': 42
}

avro_producer.produce(
    topic='supplier-reliability-score',
    value=value
)
avro_producer.flush()
```

### **3. Consume with Avro**

```python
from confluent_kafka.avro import AvroConsumer

# Create consumer with Schema Registry
avro_consumer = AvroConsumer({
    'bootstrap.servers': 'localhost:19093',
    'group.id': 'my-consumer-group',
    'schema.registry.url': 'http://localhost:18081',
    'auto.offset.reset': 'earliest'
})

avro_consumer.subscribe(['supplier-reliability-score'])

while True:
    msg = avro_consumer.poll(1.0)
    if msg is None:
        continue
    if msg.error():
        print(f"Error: {msg.error()}")
        continue
    
    # Message automatically deserialized using schema from registry
    value = msg.value()
    print(f"Supplier {value['supplier_id']}: score = {value['reliability_score']}")
```

---

## 🤖 **Agent Integration**

### **Product Generator Agent Schema Creation**

When the **Product Generator Agent** creates a new data product, it should:

1. **Generate Avro schema** based on source streams and business requirements
2. **Register schema** in Schema Registry with appropriate compatibility mode
3. **Create Kafka topic** with schema validation enabled
4. **Generate Flink SQL** that outputs Avro-serialized data
5. **Store schema metadata** in Product Service

```python
# In Product Generator Agent
async def generate_data_product(self, suggestion: Dict[str, Any]):
    """Generate complete data product with Avro schema"""
    
    # 1. Generate Avro schema using LLM
    schema = await self.generate_avro_schema(suggestion)
    
    # 2. Register in Schema Registry
    schema_id = await self.register_schema(
        subject=f"{suggestion['product_name']}-value",
        schema=schema,
        compatibility='BACKWARD'
    )
    
    # 3. Create Kafka topic with schema validation
    await self.create_topic(
        topic_name=suggestion['product_name'],
        schema_id=schema_id
    )
    
    # 4. Generate Flink SQL with Avro output
    flink_sql = await self.generate_flink_sql(
        suggestion=suggestion,
        output_schema=schema
    )
    
    # 5. Store in Product Service
    product = {
        'name': suggestion['product_name'],
        'schema': schema,
        'schema_id': schema_id,
        'output_topic': suggestion['product_name'],
        'transformations': {'flink_sql': flink_sql}
    }
    
    return product
```

---

## 📐 **Schema Design Best Practices**

### **1. Use Logical Types**
```json
{
  "name": "created_at",
  "type": {
    "type": "long",
    "logicalType": "timestamp-millis"
  }
}
```

### **2. Document Everything**
```json
{
  "name": "revenue",
  "type": "double",
  "doc": "Total revenue in USD. Null if calculation failed.",
  "default": null
}
```

### **3. Use Namespaces**
```json
{
  "type": "record",
  "name": "SupplierScore",
  "namespace": "com.platform.supplychain.v1"
}
```

### **4. Version in Namespace**
```json
"namespace": "com.platform.supplychain.v1"  // v1, v2, etc.
```

### **5. Provide Defaults for New Fields**
```json
{
  "name": "new_field",
  "type": ["null", "string"],
  "default": null  // Required for backward compatibility
}
```

---

## 🔄 **Schema Evolution Example**

### **Version 1**
```json
{
  "type": "record",
  "name": "SupplierScore",
  "namespace": "com.platform.supplychain.v1",
  "fields": [
    {"name": "supplier_id", "type": "string"},
    {"name": "score", "type": "double"}
  ]
}
```

### **Version 2 (Backward Compatible)**
```json
{
  "type": "record",
  "name": "SupplierScore",
  "namespace": "com.platform.supplychain.v1",
  "fields": [
    {"name": "supplier_id", "type": "string"},
    {"name": "score", "type": "double"},
    {"name": "region", "type": ["null", "string"], "default": null}  // New field
  ]
}
```

Old consumers can still read new messages (they ignore `region`).
New consumers can read old messages (`region` is null).

---

## 🛡️ **Schema Registry Configuration**

### **Set Compatibility Mode**
```bash
# Set global compatibility
curl -X PUT http://localhost:18081/config \
  -H "Content-Type: application/json" \
  -d '{"compatibility": "BACKWARD"}'

# Set per-subject compatibility
curl -X PUT http://localhost:18081/config/supplier-reliability-score-value \
  -H "Content-Type: application/json" \
  -d '{"compatibility": "FULL"}'
```

### **Compatibility Modes**
- `BACKWARD`: Consumers using new schema can read old data
- `FORWARD`: Consumers using old schema can read new data
- `FULL`: Both backward and forward compatible
- `NONE`: No compatibility checks (not recommended)
- `BACKWARD_TRANSITIVE`: Backward compatible with ALL previous versions
- `FORWARD_TRANSITIVE`: Forward compatible with ALL previous versions
- `FULL_TRANSITIVE`: Both, across ALL versions

---

## 📊 **Flink Integration with Avro**

### **Flink SQL with Avro Format**

```sql
-- Create source table reading Avro
CREATE TABLE supplier_events (
  supplier_id STRING,
  event_time TIMESTAMP(3),
  quality_pass BOOLEAN,
  on_time BOOLEAN,
  WATERMARK FOR event_time AS event_time - INTERVAL '5' SECOND
) WITH (
  'connector' = 'kafka',
  'topic' = 'supplier-events',
  'properties.bootstrap.servers' = 'kafka:9092',
  'format' = 'avro-confluent',
  'avro-confluent.url' = 'http://schema-registry:8081'
);

-- Create sink table writing Avro
CREATE TABLE supplier_reliability_score (
  supplier_id STRING,
  window_end TIMESTAMP(3),
  quality_acceptance_rate DOUBLE,
  on_time_delivery_rate DOUBLE,
  reliability_score DOUBLE,
  delivery_count BIGINT
) WITH (
  'connector' = 'kafka',
  'topic' = 'supplier-reliability-score',
  'properties.bootstrap.servers' = 'kafka:9092',
  'format' = 'avro-confluent',
  'avro-confluent.url' = 'http://schema-registry:8081',
  'avro-confluent.schema' = '{
    "type": "record",
    "name": "SupplierReliabilityScore",
    "namespace": "com.platform.supplychain",
    "fields": [...]
  }'
);

-- Aggregation query
INSERT INTO supplier_reliability_score
SELECT 
  supplier_id,
  TUMBLE_END(event_time, INTERVAL '1' HOUR) as window_end,
  AVG(CASE WHEN quality_pass THEN 1.0 ELSE 0.0 END) as quality_acceptance_rate,
  AVG(CASE WHEN on_time THEN 1.0 ELSE 0.0 END) as on_time_delivery_rate,
  (AVG(CASE WHEN quality_pass THEN 1.0 ELSE 0.0 END) * 0.6 +
   AVG(CASE WHEN on_time THEN 1.0 ELSE 0.0 END) * 0.4) * 100 as reliability_score,
  COUNT(*) as delivery_count
FROM supplier_events
GROUP BY supplier_id, TUMBLE(event_time, INTERVAL '1' HOUR);
```

---

## ✅ **Verification Checklist**

For every new data product:

- [ ] Avro schema defined with proper namespace
- [ ] Schema registered in Schema Registry
- [ ] Compatibility mode set appropriately
- [ ] All fields documented with `doc` attribute
- [ ] Logical types used for dates/timestamps
- [ ] Default values provided for optional fields
- [ ] Kafka topic created
- [ ] Flink job outputs Avro format
- [ ] Consumers configured to use Schema Registry
- [ ] Schema stored in Product Service metadata

---

## 🎯 **Summary**

**Every data product = Kafka topic + Avro schema + Schema Registry entry**

This ensures:
1. **Type safety** - Can't send wrong data
2. **Evolution** - Can update schemas safely
3. **Documentation** - Schema is the contract
4. **Governance** - Centralized management
5. **Quality** - Validation at serialization

**No exceptions. No raw JSON. Avro everywhere.** 🎯
