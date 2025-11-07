# Data Intelligence System

**AI-Powered Discovery, Analysis, and Governance of Your Data Ecosystem**

This system solves the real problem: bringing intelligence to the chaos of unmanaged Kafka topics, Flink streams, and ML model outputs.

---

## 🎯 The Problem It Solves

### **Before (Data Chaos):**
```
❌ Team A creates "supplier-data" (no schema)
❌ Team B creates "supplier_events" (different schema)
❌ Team C creates "suppliers-master" (yet another)
❌ Flink job outputs to "processed-suppliers"
❌ ML model writes to "supplier-predictions"

Result:
• 5 redundant topics
• No schema governance
• No one knows what exists
• Teams keep reinventing the wheel
```

### **After (Intelligent Platform):**
```
✅ Platform discovers ALL 5 topics automatically
✅ AI analyzes schemas and finds 80% overlap
✅ Platform says: "These are redundant!"
✅ Suggests: Unified data product with governed schema
✅ User approves → Platform consolidates
✅ Quality monitoring enabled automatically
```

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────┐
│       Topic Discovery Agent                 │
│  (Scans Kafka, infers schemas, tracks usage)│
└────────────────┬────────────────────────────┘
                 ↓
┌─────────────────────────────────────────────┐
│    Schema Similarity Analyzer (AI)          │
│  (Detects overlap, suggests consolidation)  │
└────────────────┬────────────────────────────┘
                 ↓
┌─────────────────────────────────────────────┐
│       Enhanced Catalog API                  │
│  (Unified view: Managed + Discovered)       │
└────────────────┬────────────────────────────┘
                 ↓
         Backstage Portal
      (User-friendly interface)
```

---

## 🚀 Quick Start

```bash
# Install
pip install confluent-kafka anthropic fastapi uvicorn requests

# Set environment
export ANTHROPIC_API_KEY="your-key"
export KAFKA_BOOTSTRAP_SERVERS="localhost:19093"

# Run discovery
cd discovery-agent
python topic_discovery.py

# Run analysis
cd ../analyzer
python schema_analyzer.py

# Start API
cd ../enhanced-catalog
python catalog_api.py
# Opens on http://localhost:8004
```

---

## 🎬 User Experience

### **Search for Data:**
```bash
curl -X POST http://localhost:8004/search -d '{
  "query": "supplier"
}'
```

**Response shows:**
- ✅ Managed products (governed)
- ⚠️ Discovered topics (unmanaged)
- 🤖 AI recommendations
- Quality scores

### **Get Recommendations:**
```bash
curl http://localhost:8004/recommendations
```

**AI suggests:**
- Topics to consolidate
- Schemas to govern
- Quality issues to fix

### **Promote Topic:**
```bash
curl -X POST http://localhost:8004/promote -d '{
  "topic_name": "supplier-events",
  "product_name": "Supplier Data Product",
  "owner": "data-team",
  "description": "Governed supplier data"
}'
```

**Result:**
- Schema registered
- Product created
- Monitoring enabled

---

## 📊 What You Get

### **Complete Visibility:**
```
Dashboard shows:
├─ 45 Total Data Sources
│  ├─ 20 Managed Products ✅
│  └─ 25 Discovered Topics
│     ├─ 15 Unmanaged ⚠️
│     └─ 10 Candidates for Governance
├─ 8 Consolidation Opportunities 🔄
└─ 67% Governance Coverage
```

### **AI Recommendations:**
```
🤖 Priority Actions:

HIGH:
• Consolidate "supplier-data" + "supplier_events" (85% overlap)
• Govern "ml-model-output-v3" (no schema, high usage)

MEDIUM:
• Archive "test-data-stream" (no activity 90 days)
• Fix "order-events" (missing required fields)

LOW:
• Promote "processed-suppliers" (good quality, no governance)
```

---

## 🎯 Key Features

✅ **Auto-Discovery** - Finds ALL topics automatically  
✅ **Schema Inference** - Infers schemas from actual data  
✅ **AI Analysis** - Detects redundancy and overlap  
✅ **Smart Recommendations** - Suggests consolidation  
✅ **Unified Catalog** - Shows managed + discovered  
✅ **Quality Scoring** - Assesses data quality  
✅ **One-Click Governance** - Promote to managed product  

---

## 🔗 Integration

### **With Product Generator:**
```python
# When user searches, show:
# 1. Existing data sources (don't recreate!)
# 2. If nothing exists, generate new product
```

### **With Backstage:**
```typescript
// Show in catalog:
<DataSource
  name="supplier-events"
  status="UNMANAGED"
  quality={67.5}
  recommendation="Promote to managed product"
/>
```

---

## 📚 Files

```
data-intelligence-system/
├── discovery-agent/
│   └── topic_discovery.py      # Discovers all topics
├── analyzer/
│   └── schema_analyzer.py      # AI-powered analysis
├── enhanced-catalog/
│   └── catalog_api.py          # REST API
└── README.md                   # This file
```

---

## 🎉 This Is What You Needed!

Users can now:
- 🔍 Search ALL data (not just managed products)
- 🤖 Get AI recommendations
- ⚠️ See quality issues
- ✅ Promote unmanaged topics to governance
- 🔄 Consolidate redundant topics

**This brings intelligence to your data chaos!** 🚀
