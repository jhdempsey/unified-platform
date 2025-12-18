# Confluent Cloud Flink Setup Guide

This guide covers setting up Apache Flink on Confluent Cloud for the Unified Platform.

## Prerequisites

- Confluent Cloud account with Kafka cluster already running
- Confluent CLI installed (`brew install confluentinc/tap/cli`)
- Environment and cluster IDs from your existing Kafka setup

## 1. Enable Flink in Confluent Cloud

### Via Confluent Cloud UI

1. Log into [Confluent Cloud](https://confluent.cloud)
2. Navigate to your Environment
3. Click **Flink** in the left sidebar
4. Click **Create compute pool**
5. Configure:
   - **Name**: `unified-platform-flink`
   - **Cloud Provider**: Azure (same as your Kafka cluster)
   - **Region**: East US (same as your Kafka cluster)
   - **Max CFUs**: Start with 5 (can scale later)
6. Click **Create**

### Via Confluent CLI

```bash
# Login to Confluent Cloud
confluent login

# List environments
confluent environment list

# Set environment
confluent environment use <env-id>

# Create Flink compute pool
confluent flink compute-pool create unified-platform-flink \
  --cloud azure \
  --region eastus \
  --max-cfu 5
```

## 2. Access Flink SQL Workspace

1. In Confluent Cloud, go to **Flink** → **Workspaces**
2. Click **Open SQL workspace**
3. Select your compute pool and Kafka cluster
4. The workspace connects to your Schema Registry automatically

## 3. Create Flink SQL Tables

Flink SQL tables map to your existing Kafka topics. Run these statements in the SQL workspace:

### Orders Table
```sql
-- Create table for order events
CREATE TABLE orders (
  order_id STRING,
  customer_id STRING,
  product_id STRING,
  quantity INT,
  unit_price DOUBLE,
  total_amount DOUBLE,
  order_status STRING,
  warehouse_id STRING,
  region STRING,
  order_timestamp TIMESTAMP(3),
  WATERMARK FOR order_timestamp AS order_timestamp - INTERVAL '5' SECOND
) WITH (
  'connector' = 'kafka',
  'topic' = 'order-events',
  'scan.startup.mode' = 'latest-offset'
);
```

### Products Table
```sql
-- Create table for product events
CREATE TABLE products (
  product_id STRING,
  product_name STRING,
  category STRING,
  supplier_id STRING,
  unit_cost DOUBLE,
  stock_level INT,
  reorder_point INT,
  last_updated TIMESTAMP(3)
) WITH (
  'connector' = 'kafka',
  'topic' = 'product-events',
  'scan.startup.mode' = 'latest-offset'
);
```

### Supplier Events Table
```sql
-- Create table for supplier events
CREATE TABLE suppliers (
  supplier_id STRING,
  supplier_name STRING,
  reliability_score DOUBLE,
  avg_delivery_days INT,
  region STRING,
  last_updated TIMESTAMP(3)
) WITH (
  'connector' = 'kafka',
  'topic' = 'supplier-events',
  'scan.startup.mode' = 'latest-offset'
);
```

## 4. Stream Processing Queries

### Real-Time Order Aggregations

```sql
-- Orders per minute by region (tumbling window)
CREATE TABLE orders_per_minute_by_region WITH (
  'connector' = 'kafka',
  'topic' = 'supply-chain.orders-aggregated'
) AS
SELECT 
  region,
  TUMBLE_START(order_timestamp, INTERVAL '1' MINUTE) as window_start,
  TUMBLE_END(order_timestamp, INTERVAL '1' MINUTE) as window_end,
  COUNT(*) as order_count,
  SUM(total_amount) as total_revenue,
  AVG(total_amount) as avg_order_value
FROM orders
GROUP BY 
  region,
  TUMBLE(order_timestamp, INTERVAL '1' MINUTE);
```

### Hourly Revenue Dashboard

```sql
-- Hourly revenue aggregation
CREATE TABLE hourly_revenue WITH (
  'connector' = 'kafka',
  'topic' = 'supply-chain.hourly-revenue'
) AS
SELECT 
  TUMBLE_START(order_timestamp, INTERVAL '1' HOUR) as hour_start,
  COUNT(*) as total_orders,
  SUM(total_amount) as total_revenue,
  COUNT(DISTINCT customer_id) as unique_customers,
  AVG(quantity) as avg_items_per_order
FROM orders
GROUP BY 
  TUMBLE(order_timestamp, INTERVAL '1' HOUR);
```

### Enriched Orders (Stream-Table Join)

```sql
-- Enrich orders with product details
CREATE TABLE enriched_orders WITH (
  'connector' = 'kafka',
  'topic' = 'supply-chain.enriched-orders'
) AS
SELECT 
  o.order_id,
  o.customer_id,
  o.product_id,
  p.product_name,
  p.category,
  o.quantity,
  o.unit_price,
  o.total_amount,
  p.supplier_id,
  o.region,
  o.order_timestamp
FROM orders o
LEFT JOIN products FOR SYSTEM_TIME AS OF o.order_timestamp AS p
  ON o.product_id = p.product_id;
```

### Low Stock Alerts

```sql
-- Generate alerts for low stock products
CREATE TABLE low_stock_alerts WITH (
  'connector' = 'kafka',
  'topic' = 'supply-chain.alerts'
) AS
SELECT 
  product_id,
  product_name,
  category,
  stock_level,
  reorder_point,
  'LOW_STOCK' as alert_type,
  CONCAT('Product ', product_name, ' stock (', CAST(stock_level AS STRING), 
         ') below reorder point (', CAST(reorder_point AS STRING), ')') as alert_message,
  CURRENT_TIMESTAMP as alert_timestamp
FROM products
WHERE stock_level < reorder_point;
```

### High Value Order Detection

```sql
-- Detect unusually large orders (potential fraud or bulk orders)
CREATE TABLE high_value_orders WITH (
  'connector' = 'kafka',
  'topic' = 'supply-chain.alerts'
) AS
SELECT 
  order_id,
  customer_id,
  total_amount,
  quantity,
  'HIGH_VALUE_ORDER' as alert_type,
  CONCAT('Large order detected: $', CAST(total_amount AS STRING), 
         ' with ', CAST(quantity AS STRING), ' items') as alert_message,
  order_timestamp as alert_timestamp
FROM orders
WHERE total_amount > 10000 OR quantity > 100;
```

### Rolling Average Fulfillment (for ML Consumer)

```sql
-- Calculate rolling statistics for ML predictions
CREATE TABLE order_statistics WITH (
  'connector' = 'kafka',
  'topic' = 'supply-chain.predictions'
) AS
SELECT 
  region,
  HOP_START(order_timestamp, INTERVAL '5' MINUTE, INTERVAL '1' HOUR) as window_start,
  COUNT(*) as order_count,
  AVG(total_amount) as avg_order_value,
  AVG(quantity) as avg_quantity,
  MAX(total_amount) as max_order_value
FROM orders
GROUP BY 
  region,
  HOP(order_timestamp, INTERVAL '5' MINUTE, INTERVAL '1' HOUR);
```

## 5. Monitor Flink Jobs

### Via UI
1. Go to **Flink** → **Statements**
2. View running statements, their status, and resource usage
3. Click on a statement to see metrics and logs

### Via CLI
```bash
# List Flink statements
confluent flink statement list

# Describe a specific statement
confluent flink statement describe <statement-name>

# Stop a statement
confluent flink statement delete <statement-name>
```

## 6. Topics Created by Flink

After running the above statements, these new topics will be created:

| Topic | Description | Retention |
|-------|-------------|-----------|
| `supply-chain.orders-aggregated` | Orders per minute by region | 7 days |
| `supply-chain.hourly-revenue` | Hourly revenue stats | 30 days |
| `supply-chain.enriched-orders` | Orders with product details | 7 days |
| `supply-chain.alerts` | Low stock and anomaly alerts | 7 days |
| `supply-chain.predictions` | Rolling stats for ML | 7 days |

## 7. Integration with Platform Services

### ML Consumer
The ML Consumer service reads from `supply-chain.predictions` for feature engineering:
```python
# In ml-consumer, consume from Flink-processed topic
KAFKA_TOPICS = "supply-chain.predictions,supply-chain.orders"
```

### Stream Analysis Service
Update to read from Flink aggregated topics:
```python
# stream-analysis can now use pre-aggregated data
KAFKA_TOPICS = "supply-chain.orders-aggregated,supply-chain.alerts"
```

### Dashboard
The dashboard can display Flink-computed metrics:
- Real-time revenue (from `hourly_revenue`)
- Alert counts (from `supply-chain.alerts`)
- Order trends (from `orders-aggregated`)

## 8. Cost Considerations

Confluent Cloud Flink pricing is based on CFUs (Confluent Flink Units):

| CFUs | Use Case | Est. Cost/Month |
|------|----------|-----------------|
| 5 | Development/Testing | ~$250 |
| 10 | Light Production | ~$500 |
| 20 | Medium Production | ~$1,000 |

Tips to optimize:
- Start with 5 CFUs and scale as needed
- Use tumbling windows instead of sliding when possible
- Limit the number of concurrent statements
- Use appropriate watermark strategies

## 9. Terraform Integration (Partial Support)

While Confluent provider supports some Flink resources, compute pools and statements 
are best managed via UI/CLI. Here's what can be automated:

```hcl
# In a separate confluent.tf file (requires Confluent Terraform provider)
terraform {
  required_providers {
    confluent = {
      source  = "confluentinc/confluent"
      version = "~> 1.55"
    }
  }
}

provider "confluent" {
  cloud_api_key    = var.confluent_cloud_api_key
  cloud_api_secret = var.confluent_cloud_api_secret
}

# Reference existing environment
data "confluent_environment" "main" {
  id = var.confluent_environment_id
}

# Note: Flink compute pools are not yet fully supported in Terraform
# Use CLI or UI to create compute pools
```

## 10. Troubleshooting

### Statement Won't Start
- Check CFU availability in compute pool
- Verify topic names match exactly
- Ensure Schema Registry is accessible

### No Data Flowing
- Verify source topics have data: `confluent kafka topic consume <topic>`
- Check watermark configuration
- Verify timestamp fields are populated

### High Latency
- Increase CFUs in compute pool
- Optimize window sizes
- Check for data skew in partition keys

## Architecture with Flink

```
┌─────────────────────────────────────────────────────────────────┐
│                     Confluent Cloud                              │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                    Kafka Cluster                            │ │
│  │  order-events  product-events  supplier-events              │ │
│  └──────────────────────────┬──────────────────────────────────┘ │
│                             │                                    │
│  ┌──────────────────────────▼──────────────────────────────────┐ │
│  │                 Flink Compute Pool                          │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │ │
│  │  │  Aggregate  │  │   Enrich    │  │   Detect    │         │ │
│  │  │   Orders    │  │   Orders    │  │   Alerts    │         │ │
│  │  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘         │ │
│  └─────────┼────────────────┼────────────────┼─────────────────┘ │
│            │                │                │                   │
│  ┌─────────▼────────────────▼────────────────▼─────────────────┐ │
│  │                    Output Topics                            │ │
│  │  orders-aggregated  enriched-orders  alerts  predictions    │ │
│  └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                             │
            ┌────────────────┼────────────────┐
            ▼                ▼                ▼
     ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
     │ ML Consumer │  │  Dashboard  │  │   Stream    │
     │   (GCP)     │  │   (GCP)     │  │  Analysis   │
     └─────────────┘  └─────────────┘  └─────────────┘
```
