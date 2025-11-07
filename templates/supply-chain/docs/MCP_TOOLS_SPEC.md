# MCP Tools - Required for Platform

## Schema Management Tools

### `register_avro_schema`
**Description**: Register an Avro schema in Confluent Schema Registry

**Parameters**:
```json
{
  "subject": "string (e.g., 'supplier-reliability-score-value')",
  "schema": "string (JSON Avro schema)",
  "compatibility": "string (optional: BACKWARD, FORWARD, FULL, NONE)"
}
```

**Returns**:
```json
{
  "schema_id": 1,
  "version": 1,
  "subject": "supplier-reliability-score-value"
}
```

---

### `get_schema_by_id`
**Description**: Retrieve schema from registry by ID

**Parameters**:
```json
{
  "schema_id": "integer"
}
```

**Returns**:
```json
{
  "schema": "{...avro schema...}",
  "schema_type": "AVRO"
}
```

---

### `list_subjects`
**Description**: List all registered schema subjects

**Returns**:
```json
{
  "subjects": [
    "supplier-reliability-score-value",
    "supplier-events-value"
  ]
}
```

---

### `get_latest_schema`
**Description**: Get latest version of schema for subject

**Parameters**:
```json
{
  "subject": "string"
}
```

**Returns**:
```json
{
  "subject": "supplier-reliability-score-value",
  "version": 2,
  "schema_id": 3,
  "schema": "{...avro schema...}"
}
```

---

### `validate_schema_compatibility`
**Description**: Check if new schema is compatible with existing

**Parameters**:
```json
{
  "subject": "string",
  "schema": "string (new schema to test)"
}
```

**Returns**:
```json
{
  "is_compatible": true
}
```

---

## Kafka Topic Tools

### `create_kafka_topic`
**Description**: Create Kafka topic with Avro schema validation

**Parameters**:
```json
{
  "topic_name": "string",
  "partitions": "integer (default: 3)",
  "replication_factor": "integer (default: 1)",
  "schema_subject": "string (optional, for validation)"
}
```

---

### `analyze_kafka_streams`
**Description**: Analyze Kafka topics for patterns (existing tool, enhanced)

**Parameters**:
```json
{
  "lookback_days": "integer",
  "include_schemas": "boolean",
  "include_query_patterns": "boolean"
}
```

**Enhanced Returns**:
```json
{
  "topics": [
    {
      "name": "supplier-events",
      "schema_id": 1,
      "schema_subject": "supplier-events-value",
      "message_count": 150000,
      "avg_message_size": 512
    }
  ],
  "join_patterns": [...],
  "transformation_patterns": [...]
}
```

---

## Data Product Generation Tools

### `generate_avro_schema`
**Description**: Use LLM to generate Avro schema from description

**Parameters**:
```json
{
  "product_name": "string",
  "description": "string",
  "source_streams": ["array of topic names"],
  "business_requirements": "string"
}
```

**Returns**:
```json
{
  "schema": "{...generated avro schema...}",
  "namespace": "com.platform.domain.v1",
  "reasoning": "Schema includes fields X, Y, Z because..."
}
```

---

### `generate_flink_sql`
**Description**: Generate Flink SQL with Avro output format

**Parameters**:
```json
{
  "product_name": "string",
  "source_streams": ["array"],
  "output_schema": "string (Avro schema)",
  "aggregation_window": "string (e.g., '1 HOUR')"
}
```

**Returns**:
```json
{
  "create_source_tables": "SQL...",
  "create_sink_table": "SQL with avro-confluent format...",
  "transformation_query": "SQL..."
}
```

---

## Implementation Priority

### Phase 1 (Week 1-2)
- [ ] `register_avro_schema`
- [ ] `get_latest_schema`
- [ ] `create_kafka_topic` (enhanced with schema)
- [ ] `analyze_kafka_streams` (enhance existing)

### Phase 2 (Week 3-4)
- [ ] `generate_avro_schema` (LLM-powered)
- [ ] `validate_schema_compatibility`
- [ ] `generate_flink_sql` (LLM-powered)

### Phase 3 (Week 5-6)
- [ ] `get_schema_by_id`
- [ ] `list_subjects`
- [ ] Quality validation tools

---

## Example Agent Flow

```python
# Stream Analysis Agent detects pattern
suggestion = {
    'product_name': 'supplier-reliability-score',
    'source_streams': ['supplier-events', 'quality-inspections']
}

# Send to Product Generator Agent via A2A
await stream_agent.send_to_agent(
    recipient_id='product-generator-agent',
    intent='suggest_product',
    payload={'suggestion': suggestion}
)

# Product Generator Agent receives and calls MCP tools
async def handle_suggest_product(message):
    suggestion = message.payload['suggestion']
    
    # 1. Generate Avro schema
    schema = await self.call_mcp_tool(
        'generate_avro_schema',
        {
            'product_name': suggestion['product_name'],
            'source_streams': suggestion['source_streams'],
            'business_requirements': 'Track supplier reliability'
        }
    )
    
    # 2. Register schema
    registration = await self.call_mcp_tool(
        'register_avro_schema',
        {
            'subject': f"{suggestion['product_name']}-value",
            'schema': schema['schema'],
            'compatibility': 'BACKWARD'
        }
    )
    
    # 3. Create topic
    await self.call_mcp_tool(
        'create_kafka_topic',
        {
            'topic_name': suggestion['product_name'],
            'partitions': 3,
            'schema_subject': registration['subject']
        }
    )
    
    # 4. Generate Flink SQL
    flink_sql = await self.call_mcp_tool(
        'generate_flink_sql',
        {
            'product_name': suggestion['product_name'],
            'source_streams': suggestion['source_streams'],
            'output_schema': schema['schema']
        }
    )
    
    # 5. Send to Business Context Agent for validation
    await self.send_to_agent(
        recipient_id='business-context-agent',
        intent='validate_product',
        payload={
            'product': {
                'name': suggestion['product_name'],
                'schema': schema['schema'],
                'schema_id': registration['schema_id'],
                'flink_sql': flink_sql
            }
        }
    )
```
