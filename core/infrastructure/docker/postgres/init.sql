-- Initialize platform database
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create tables for lineage tracking
CREATE TABLE IF NOT EXISTS data_lineage (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_topic VARCHAR(255),
    target_topic VARCHAR(255),
    transformation_type VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create tables for quality metrics
CREATE TABLE IF NOT EXISTS quality_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    topic VARCHAR(255),
    metric_name VARCHAR(100),
    metric_value FLOAT,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_lineage_source ON data_lineage(source_topic);
CREATE INDEX IF NOT EXISTS idx_lineage_target ON data_lineage(target_topic);
CREATE INDEX IF NOT EXISTS idx_quality_topic ON quality_metrics(topic);
