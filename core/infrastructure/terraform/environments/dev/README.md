# Development Environment

This directory contains Terraform configuration for the **development** environment.

## 🚀 Quick Start

```bash
cd infrastructure/terraform/environments/dev

# Initialize
terraform init

# Review changes
terraform plan

# Apply
terraform apply
```

## 📝 Configuration

### **terraform.tfvars** (Create this file)

```hcl
project_id = "platform-dev-20251026-v2"
region     = "us-central1"
zone       = "us-central1-a"

# Override defaults as needed
# gke_node_count    = 3
# gke_machine_type  = "e2-standard-4"
# gke_preemptible   = true
```

**Note**: `terraform.tfvars` is gitignored for security.

## 🏗️ What Gets Created

### **Phase 1: Core** (Current)
- ✅ Enabled GCP APIs
- ✅ Service accounts (platform-dev-sa, platform-gke-workload)
- ✅ IAM role bindings
- ✅ Secret Manager secrets (empty, add values manually)

### **Phase 2: Network** (Uncomment in main.tf)
- ⏳ VPC network
- ⏳ Subnets
- ⏳ Cloud NAT
- ⏳ Firewall rules

### **Phase 3: GKE** (Uncomment in main.tf)
- ⏳ GKE cluster
- ⏳ Node pools
- ⏳ Workload Identity

## 🔐 After Applying

### **1. Create Service Account Key**

```bash
gcloud iam service-accounts keys create ~/platform-dev-sa.json \
  --iam-account=platform-dev-sa@platform-dev-20251026-v2.iam.gserviceaccount.com
```

### **2. Add Secret Values**

```bash
# Anthropic
echo -n "sk-ant-..." | gcloud secrets versions add anthropic-api-key --data-file=-

# OpenAI
echo -n "sk-..." | gcloud secrets versions add openai-api-key --data-file=-

# Gemini (optional)
echo -n "..." | gcloud secrets versions add gemini-api-key --data-file=-
```

### **3. Update Local .env**

```bash
# Add to project root .env
GOOGLE_APPLICATION_CREDENTIALS=/Users/jhdempsey/.config/gcloud/platform-dev-sa.json
GCP_PROJECT_ID=platform-dev-20251026-v2
GCP_REGION=us-central1
```

## 📊 Estimated Costs

**Current (Phase 1)**: ~$0/month
- Just API enablement and service accounts

**With GKE (Phase 3)**: ~$75/month
- 3 x e2-standard-4 preemptible nodes
- Can reduce to 1 node for ~$25/month

## 🔄 Deploying Network & GKE

When ready:

```bash
# 1. Edit main.tf, uncomment network module
# 2. Edit main.tf, uncomment gke module

# 3. Apply
terraform apply
```

## 🆘 Troubleshooting

### **"Billing not enabled"**

```bash
# Link billing account
gcloud billing projects link platform-dev-20251026-v2 \
  --billing-account=018DA9-451650-8109DD
```

### **"API not enabled"**

```bash
# Wait for APIs to enable (takes 1-2 minutes)
# Or enable manually:
gcloud services enable container.googleapis.com
```

### **"Permission denied"**

```bash
# Re-authenticate
gcloud auth application-default login
gcloud auth application-default set-quota-project platform-dev-20251026-v2
```

## 📚 Module Documentation

Modules are defined in `../../modules/`:
- `project/` - Project setup, service accounts, IAM
- `secrets/` - Secret Manager configuration
- `network/` - VPC, subnets, firewall rules
- `gke/` - GKE cluster configuration

See each module's README for details.
