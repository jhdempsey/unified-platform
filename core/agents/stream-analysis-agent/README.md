# Stream Analysis Agent

AI-powered real-time data quality monitoring agent.

## 🚀 Quick Start

### **Install Dependencies**

```bash
pip install confluent-kafka anthropic
```

### **Set Environment Variables**

```bash
export KAFKA_BOOTSTRAP_SERVERS="localhost:19093"
export SCHEMA_REGISTRY_URL="http://localhost:18081"
export ANTHROPIC_API_KEY="your-api-key-here"  # Optional - uses rule-based if not set
```

### **Run the Agent**

```bash
python main.py
```

---

## 🤖 What It Does

The Stream Analysis Agent:

1. **Consumes** events from Kafka topics (`supplier-events`, `order-events`, `product-events`)
2. **Analyzes** data quality using AI (Claude) or rule-based algorithms
3. **Detects** anomalies, missing data, schema violations
4. **Produces** quality alerts to the `quality-alerts` topic

---

## 📊 Analysis Flow

```
Kafka Topics
  ↓
Consumer (kafka_consumer.py)
  ↓
Batch Messages
  ↓
AI Analyzer (analyzer.py)
  ↓
Quality Analysis
  ↓
Alert Decision
  ↓
Alert Producer (alert_producer.py)
  ↓
quality-alerts Topic
```

---

## 🧠 AI Analysis

### **With Claude API (Recommended)**

Set `ANTHROPIC_API_KEY` environment variable.

The agent uses Claude to:
- Detect data quality issues
- Identify anomalies and patterns
- Provide actionable recommendations
- Calculate quality scores

### **Without API (Rule-Based Fallback)**

If no API key is set, uses rule-based analysis:
- Check for missing fields
- Detect null values
- Monitor message rates
- Basic quality scoring

---

## 🚨 Alert Types

The agent produces alerts for:

- **ANOMALY** - Unusual patterns in data
- **MISSING_DATA** - Missing required fields
- **SCHEMA_VIOLATION** - Data doesn't match expected schema
- **THRESHOLD_BREACH** - Quality metrics below threshold
- **DATA_DRIFT** - Significant changes in data distribution

### **Severity Levels**

- **LOW** - Quality score 90-100
- **MEDIUM** - Quality score 75-89
- **HIGH** - Quality score 50-74
- **CRITICAL** - Quality score <50

---

## 📤 Alert Format

Alerts are published to `quality-alerts` topic:

```json
{
  "event_id": "uuid",
  "alert_type": "ANOMALY",
  "severity": "MEDIUM",
  "product_id": "PROD-SUPPLIER-EVENTS",
  "topic_name": "supplier-events",
  "description": "Analyzed 50 messages. Quality score: 82.5",
  "ai_analysis": "Continue monitoring\nValidate upstream data sources",
  "affected_records": 50,
  "metrics": {
    "quality_score": 82.5,
    "analyzed_messages": 50.0
  },
  "timestamp": 1234567890,
  "detection_method": "AI_AGENT"
}
```

---

## 🧪 Testing

### **1. Generate Test Data**

```bash
# Run the test script to produce test messages
cd ~/Work/AI_Development/platform-monorepo
python scripts/test-kafka-avro.py
```

### **2. Start the Agent**

```bash
cd services/stream-analysis-agent
python main.py
```

### **3. Check Alerts**

```bash
# Consume alerts
python << 'EOF'
from scripts.avro_consumer import AvroConsumerHelper

consumer = AvroConsumerHelper(group_id="alert-viewer")
consumer.subscribe(["quality-alerts"])

for key, value, topic, partition, offset in consumer.consume(timeout=5.0):
    print(f"\n🚨 Alert:")
    print(f"   Severity: {value['severity']}")
    print(f"   Topic: {value['topic_name']}")
    print(f"   Score: {value['metrics']['quality_score']}")
    print(f"   Analysis: {value['ai_analysis']}")
EOF
```

---

## 📊 Agent Statistics

The agent tracks:

- **Batches analyzed** - Number of message batches processed
- **Messages analyzed** - Total messages examined
- **Alerts produced** - Number of quality alerts generated

Statistics are printed on shutdown.

---

## ⚙️ Configuration

### **Batch Processing**

```python
consumer.start_consuming(
    on_batch=handler,
    batch_size=50,      # Messages per batch
    batch_interval=10.0  # Max seconds to wait
)
```

### **Topics to Monitor**

Edit `main.py`:

```python
self.topics = [
    "supplier-events",
    "order-events",
    "product-events",
    # Add more topics here
]
```

---

## 🔧 Components

### **analyzer.py**
- AI-powered analysis with Claude
- Rule-based fallback
- Quality scoring

### **kafka_consumer.py**
- Consumes from Kafka with Avro deserialization
- Batch processing
- Auto-commit

### **alert_producer.py**
- Produces alerts to Kafka
- Avro serialization
- Schema validation

### **main.py**
- Orchestrates all components
- Statistics tracking
- Signal handling

---

## 🎯 Example Output

```
🚀 STREAM ANALYSIS AGENT STARTING
📥 Monitoring topics: supplier-events, order-events, product-events
🤖 AI Analysis: Enabled

📊 Analyzing batch from supplier-events: 25 messages
   Quality Score: 95.0
   Severity: LOW
   Issues: 0
   ✅ No alert needed

📊 Analyzing batch from order-events: 30 messages
   Quality Score: 78.5
   Severity: MEDIUM
   Issues: 2
   🚨 Alert triggered!
   ✅ Alert delivered to quality-alerts [0] @ 5

📊 Final Statistics:
   Batches analyzed: 15
   Messages analyzed: 450
   Alerts produced: 3
```

---

## 🎨 Customization

### **Add Custom Analysis**

Edit `analyzer.py`:

```python
def _custom_analysis(self, messages, topic):
    # Your custom logic
    pass
```

### **Change Alert Thresholds**

Edit `analyzer.py`:

```python
def should_alert(self, analysis):
    # Custom alert logic
    return analysis["quality_score"] < 85  # Your threshold
```

---

## 📚 Next Steps

1. Start the agent: `python main.py`
2. Generate test data to analyze
3. View alerts in Kafka
4. Integrate with alerting system (email, Slack, PagerDuty)
5. Build dashboard to visualize quality metrics
