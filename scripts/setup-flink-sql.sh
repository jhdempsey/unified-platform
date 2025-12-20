#!/bin/bash
# Setup Flink SQL statements for Confluent Cloud
# Usage: ./scripts/setup-flink-sql.sh
#
# Generates SQL statements to run in Confluent Cloud Flink SQL workspace.
# Uses TVF (Table-Valued Function) syntax required by Confluent Cloud Flink.

set -e

# Configuration
ENVIRONMENT_ID="${CONFLUENT_ENVIRONMENT_ID:-env-j01z0p}"
COMPUTE_POOL_ID="${CONFLUENT_COMPUTE_POOL_ID:-lfcp-1p9vp6}"
DATABASE="${CONFLUENT_DATABASE:-unified-platform-kafka}"

cat << 'HEADER'
-- =============================================================================
-- Flink SQL Statements for Unified Platform (Confluent Cloud)
-- Run these in Confluent Cloud Flink SQL Workspace
-- 
-- IMPORTANT: Confluent Cloud Flink requires TVF (Table-Valued Function) syntax
-- for windowed aggregations, not the legacy GROUP BY TUMBLE() syntax.
-- =============================================================================

-- Set startup mode to read from beginning (for initial setup)
SET 'sql.tables.scan.startup.mode' = 'earliest-offset';

HEADER

cat << 'SQL'
-- =============================================================================
-- SIMPLE QUERIES (Run these first to verify data is flowing)
-- =============================================================================

-- Check order events
-- SELECT * FROM `order-events` LIMIT 10;

-- Count by event type
-- SELECT event_type, COUNT(*) as cnt FROM `order-events` GROUP BY event_type;

-- Sum by supplier
-- SELECT supplier_id, SUM(order_total) as revenue FROM `order-events` GROUP BY supplier_id;


-- =============================================================================
-- 1. ORDERS PER MINUTE BY REGION (1-minute Tumbling Window)
-- =============================================================================
-- Aggregates orders by region in 1-minute windows
-- Uses $rowtime (Kafka message timestamp) as the time attribute

CREATE TABLE orders_per_minute_by_region AS
SELECT 
  window_start,
  window_end,
  shipping_address.state as region,
  COUNT(*) as order_count,
  SUM(order_total) as total_revenue,
  AVG(order_total) as avg_order_value
FROM TABLE(
  TUMBLE(TABLE `order-events`, DESCRIPTOR($rowtime), INTERVAL '1' MINUTE)
)
GROUP BY window_start, window_end, shipping_address.state;


-- =============================================================================
-- 2. HOURLY REVENUE AGGREGATION (1-hour Tumbling Window)
-- =============================================================================
-- Aggregates total revenue and order statistics per hour

CREATE TABLE hourly_revenue AS
SELECT
  window_start,
  window_end,
  COUNT(*) as total_orders,
  SUM(order_total) as total_revenue,
  COUNT(DISTINCT customer_id) as unique_customers,
  COUNT(DISTINCT supplier_id) as unique_suppliers
FROM TABLE(
  TUMBLE(TABLE `order-events`, DESCRIPTOR($rowtime), INTERVAL '1' HOUR)
)
GROUP BY window_start, window_end;


-- =============================================================================
-- 3. HIGH VALUE ORDER ALERTS (Filter - no windowing)
-- =============================================================================
-- Detects orders above $500 and emits alerts in real-time

CREATE TABLE high_value_alerts AS
SELECT
  CONCAT('HV-', order_id) as alert_id,
  'HIGH_VALUE_ORDER' as alert_type,
  order_id,
  customer_id,
  supplier_id,
  order_total,
  $rowtime as alert_timestamp
FROM `order-events`
WHERE order_total > 500;


-- =============================================================================
-- 4. ORDER EVENT TYPE DISTRIBUTION (5-minute Tumbling Window)
-- =============================================================================
-- Tracks distribution of order events by type in 5-minute windows

CREATE TABLE order_event_distribution AS
SELECT
  window_start,
  window_end,
  event_type,
  COUNT(*) as event_count
FROM TABLE(
  TUMBLE(TABLE `order-events`, DESCRIPTOR($rowtime), INTERVAL '5' MINUTE)
)
GROUP BY window_start, window_end, event_type;


-- =============================================================================
-- 5. SUPPLIER PERFORMANCE METRICS (Rolling 1-hour window, sliding every 5 min)
-- =============================================================================
-- Rolling metrics per supplier using HOP (sliding) window

CREATE TABLE supplier_metrics AS
SELECT
  window_start,
  window_end,
  supplier_id,
  COUNT(*) as order_count,
  SUM(order_total) as total_revenue,
  AVG(order_total) as avg_order_value
FROM TABLE(
  HOP(TABLE `order-events`, DESCRIPTOR($rowtime), INTERVAL '5' MINUTE, INTERVAL '1' HOUR)
)
GROUP BY window_start, window_end, supplier_id;


-- =============================================================================
-- 6. REAL-TIME ORDER ENRICHMENT (No windowing - continuous)
-- =============================================================================
-- Flattens nested order data for easier downstream consumption

CREATE TABLE enriched_orders AS
SELECT
  event_id,
  event_type,
  order_id,
  supplier_id,
  customer_id,
  order_total,
  currency,
  shipping_address.city as ship_city,
  shipping_address.state as ship_state,
  shipping_address.country as ship_country,
  $rowtime as event_time,
  metadata['source'] as event_source,
  metadata['region'] as supplier_region
FROM `order-events`;


-- =============================================================================
-- 7. ORDERS BY CITY (5-minute Tumbling Window)
-- =============================================================================
-- Aggregates orders by shipping city

CREATE TABLE orders_by_city AS
SELECT
  window_start,
  window_end,
  shipping_address.city as city,
  shipping_address.state as state,
  COUNT(*) as order_count,
  SUM(order_total) as total_revenue
FROM TABLE(
  TUMBLE(TABLE `order-events`, DESCRIPTOR($rowtime), INTERVAL '5' MINUTE)
)
GROUP BY window_start, window_end, shipping_address.city, shipping_address.state;

SQL

cat << 'FOOTER'

-- =============================================================================
-- VERIFICATION QUERIES (Run after creating tables)
-- =============================================================================

-- Check orders per minute by region
-- SELECT * FROM orders_per_minute_by_region;

-- Check hourly revenue
-- SELECT * FROM hourly_revenue;

-- Check high value alerts
-- SELECT * FROM high_value_alerts;

-- Check event distribution
-- SELECT * FROM order_event_distribution;

-- Check supplier metrics
-- SELECT * FROM supplier_metrics;

-- Check enriched orders
-- SELECT * FROM enriched_orders LIMIT 10;

-- Check orders by city
-- SELECT * FROM orders_by_city;


-- =============================================================================
-- MANAGING FLINK JOBS
-- =============================================================================
-- 
-- View running statements/jobs:
--   SHOW JOBS;
--
-- Stop a job by dropping its table:
--   DROP TABLE <table_name>;
--
-- Note: Dropping the table stops the Flink job but the Kafka topic persists.
--
-- To see all tables:
--   SHOW TABLES;
--
-- =============================================================================


-- =============================================================================
-- TVF SYNTAX REFERENCE
-- =============================================================================
--
-- TUMBLING WINDOW (non-overlapping, fixed-size):
--   FROM TABLE(TUMBLE(TABLE source, DESCRIPTOR($rowtime), INTERVAL '1' MINUTE))
--   GROUP BY window_start, window_end, ...
--
-- HOPPING WINDOW (overlapping, sliding):
--   FROM TABLE(HOP(TABLE source, DESCRIPTOR($rowtime), INTERVAL '5' MINUTE, INTERVAL '1' HOUR))
--   GROUP BY window_start, window_end, ...
--   (slides every 5 minutes, window size is 1 hour)
--
-- SESSION WINDOW (gap-based):
--   FROM TABLE(SESSION(TABLE source PARTITION BY key, DESCRIPTOR($rowtime), INTERVAL '10' MINUTE))
--   GROUP BY window_start, window_end, ...
--
-- CUMULATE WINDOW (expanding):
--   FROM TABLE(CUMULATE(TABLE source, DESCRIPTOR($rowtime), INTERVAL '1' MINUTE, INTERVAL '1' HOUR))
--   GROUP BY window_start, window_end, ...
--
-- =============================================================================
FOOTER

echo ""
echo "# ============================================================================="
echo "# QUICK START GUIDE"
echo "# ============================================================================="
echo "#"
echo "# 1. Open Flink SQL Workspace:"
echo "#    https://confluent.cloud/environments/${ENVIRONMENT_ID}/flink/workspaces"
echo "#"
echo "# 2. Select:"
echo "#    - Compute pool: ${COMPUTE_POOL_ID}"
echo "#    - Catalog: default"
echo "#    - Database: ${DATABASE}"
echo "#"
echo "# 3. First, set startup mode:"
echo "#    SET 'sql.tables.scan.startup.mode' = 'earliest-offset';"
echo "#"
echo "# 4. Run a simple query to verify data:"
echo "#    SELECT * FROM \`order-events\` LIMIT 10;"
echo "#"
echo "# 5. Create aggregation tables (run one at a time):"
echo "#    CREATE TABLE orders_per_minute_by_region AS SELECT ..."
echo "#"
echo "# 6. Generate test data:"
echo "#    curl -X POST 'https://event-producer-742330383495.us-central1.run.app/produce/100?format=avro'"
echo "#"
echo "# 7. Query results:"
echo "#    SELECT * FROM orders_per_minute_by_region;"
echo "#"
echo "# ============================================================================="
