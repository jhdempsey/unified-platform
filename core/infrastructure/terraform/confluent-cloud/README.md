# Confluent Cloud Terraform Module

Terraform configuration for managing Confluent Cloud resources including Kafka, Schema Registry, and Flink.

## Overview

This module provides two approaches:

1. **New Setup** (`confluent-cloud.tf`) - Creates all resources from scratch
2. **Existing Setup** (`confluent-cloud-existing.tf`) - Adds Flink to existing Kafka cluster

## Prerequisites

1. **Confluent Cloud Account** with appropriate permissions
2. **Terraform** >= 1.0
3. **Cloud API Key** with Cloud resource management permissions

### Creating a Cloud API Key

1. Go to [Confluent Cloud API Keys](https://confluent.cloud/settings/api-keys)
2. Click "Add API key"
3. Select "Cloud resource management"
4. Select scope (Organization or specific environment)
5. Save the key and secret

## Quick Start (Existing Cluster)

If you already have a Kafka cluster running:

```bash
cd core/infrastructure/terraform/confluent-cloud

# Copy the existing resources config
cp confluent-cloud-existing.tf main.tf

# Copy and edit variables
cp terraform-existing.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your IDs

# Initialize and apply
terraform init
terraform plan
terraform apply
```

## Quick Start (New Setup)

To create everything from scratch:

```bash
cd core/infrastructure/terraform/confluent-cloud

# Copy the new setup config
cp confluent-cloud.tf main.tf

# Copy and edit variables
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your API keys

# Initialize and apply
terraform init
terraform plan
terraform apply
```

## Files

| File | Purpose |
|------|---------|
| `confluent-cloud.tf` | Creates new environment, Kafka, Schema Registry, Flink |
| `confluent-cloud-existing.tf` | Adds Flink to existing Kafka cluster |
| `confluent-flink-statements.tf` | Flink SQL statements (optional, requires provider >= 1.76) |
| `terraform.tfvars.example` | Variables for new setup |
| `terraform-existing.tfvars.example` | Variables for existing setup |

## Resources Created

### New Setup (`confluent-cloud.tf`)
- Confluent Environment
- Kafka Cluster (Basic tier)
- Schema Registry Cluster
- Flink Compute Pool
- Service Accounts (app, flink, schema-registry)
- API Keys
- Role Bindings
- Kafka Topics (9 topics)

### Existing Setup (`confluent-cloud-existing.tf`)
- Flink Compute Pool
- Flink Service Account
- Flink API Key
- Role Bindings
- Kafka Topics (9 topics)

## Kafka Topics

| Topic | Purpose | Cleanup Policy |
|-------|---------|---------------|
| `order-events` | Source: Customer orders | delete |
| `product-events` | Source: Product catalog | compact |
| `supplier-events` | Source: Supplier data | compact |
| `supply-chain.orders` | Processed orders | delete |
| `supply-chain.predictions` | ML predictions | delete |
| `supply-chain.alerts` | System alerts | delete |
| `supply-chain.orders-aggregated` | Flink: Aggregated orders | delete |
| `supply-chain.hourly-revenue` | Flink: Revenue stats | delete |
| `supply-chain.enriched-orders` | Flink: Enriched orders | delete |

## Finding Your Resource IDs

### Environment ID
1. Go to https://confluent.cloud
2. Click your environment in the left sidebar
3. Click "Settings"
4. Copy "Environment ID" (e.g., `env-abc123`)

### Kafka Cluster ID
1. Navigate to your Kafka cluster
2. Click "Cluster settings"
3. Copy "Cluster ID" (e.g., `lkc-xyz789`)

### Schema Registry ID
1. In your environment, click "Schema Registry"
2. Click "Settings"
3. Copy "Schema Registry ID" (e.g., `lsrc-123abc`)

## Flink SQL Statements

The `confluent-flink-statements.tf` file contains Flink SQL statements that can be managed via Terraform. This requires:
- Confluent Provider version >= 1.76
- Flink compute pool already created

**Note:** If you encounter issues with Terraform-managed Flink statements, you can create them manually in the Flink SQL Workspace. See `docs/CONFLUENT_FLINK_SETUP.md`.

### Available Statements
1. **Orders per minute by region** - Tumbling window aggregation
2. **Hourly revenue** - Revenue statistics
3. **Low stock alerts** - Product inventory alerts
4. **High value orders** - Large order detection

## Outputs

After `terraform apply`, you'll get:

```hcl
# Cluster information
kafka_bootstrap_server = "pkc-xxxxx.eastus.azure.confluent.cloud:9092"
schema_registry_url    = "https://psrc-xxxxx.eastus.azure.confluent.cloud"

# Flink
flink_compute_pool_id = "lfcp-xxxxx"
flink_api_key         = "XXXXX"

# API Keys for applications
app_kafka_api_key     = "XXXXX"
app_kafka_api_secret  = <sensitive>
```

## Integration with GCP

After creating Confluent resources, update GCP Secret Manager:

```bash
# Get outputs
terraform output -json > confluent-outputs.json

# Update GCP secrets
echo "$(terraform output -raw kafka_bootstrap_server)" | \
  gcloud secrets versions add confluent-bootstrap-server --data-file=-

echo "$(terraform output -raw app_kafka_api_key)" | \
  gcloud secrets versions add confluent-kafka-api-key --data-file=-

echo "$(terraform output -raw app_kafka_api_secret)" | \
  gcloud secrets versions add confluent-kafka-api-secret --data-file=-
```

## Cost Estimates

| Resource | Monthly Cost |
|----------|-------------|
| Kafka Basic Cluster | $50-200 |
| Schema Registry | Included |
| Flink (5 CFUs) | ~$250 |
| Flink (10 CFUs) | ~$500 |

## Troubleshooting

### "Unauthorized" Error
- Verify Cloud API key has correct permissions
- Check if key is for correct organization/environment

### "Resource Not Found"
- Verify resource IDs are correct
- Check if resources exist in Confluent Cloud UI

### Flink Statements Fail
- Ensure Flink compute pool is running
- Verify source topics exist and have data
- Check CFU availability

### Topic Already Exists
- Terraform will manage existing topics
- Use `lifecycle { ignore_changes }` if needed

## Import Existing Resources

To import resources created outside Terraform:

```bash
# Import environment
terraform import confluent_environment.main env-xxxxx

# Import Kafka cluster
terraform import confluent_kafka_cluster.main lkc-xxxxx

# Import topic
terraform import confluent_kafka_topic.order_events lkc-xxxxx/order-events
```

## References

- [Confluent Terraform Provider](https://registry.terraform.io/providers/confluentinc/confluent/latest/docs)
- [Confluent Cloud Flink](https://docs.confluent.io/cloud/current/flink/index.html)
- [Flink SQL Reference](https://docs.confluent.io/cloud/current/flink/reference/overview.html)
