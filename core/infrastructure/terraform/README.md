# Platform Infrastructure - Terraform

Infrastructure as Code for the Intelligent Data Product Platform on GCP.

## 📁 **New Multi-Environment Structure**

```
infrastructure/terraform/
├── environments/
│   ├── dev/           ← START HERE for development
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   ├── outputs.tf
│   │   └── README.md
│   ├── staging/       ← TODO: Configure when needed
│   └── prod/          ← TODO: Configure when needed
├── modules/
│   ├── project/       ← Service accounts, APIs
│   ├── secrets/       ← Secret Manager
│   ├── network/       ← TODO: VPC configuration
│   ├── gke/           ← TODO: GKE cluster
│   └── monitoring/    ← TODO: Observability
└── README.md          ← This file
```

## 🚀 **Quick Start (Development)**

```bash
cd infrastructure/terraform/environments/dev

# Set quota project first
gcloud auth application-default set-quota-project platform-dev-20251026-v2

# Initialize
terraform init

# Review
terraform plan

# Apply
terraform apply
```

See `environments/dev/README.md` for detailed instructions.

---

## 🔧 Configuration

### **Required Variables**

Edit `variables.tf` or create `terraform.tfvars`:

```hcl
project_id      = "platform-dev-20251026-v2"
billing_account = "018DA9-451650-8109DD"
region          = "us-central1"
environment     = "dev"
```

### **Using terraform.tfvars** (Recommended)

```bash
# Create terraform.tfvars (gitignored)
cat > terraform.tfvars << EOF
project_id      = "platform-dev-20251026-v2"
billing_account = "018DA9-451650-8109DD"
region          = "us-central1"
zone            = "us-central1-a"
environment     = "dev"

# GKE Configuration
gke_cluster_name  = "platform-cluster"
gke_node_count    = 3
gke_machine_type  = "e2-standard-4"
gke_preemptible   = true
EOF
```

---

## 📋 What Gets Created

### **Phase 1: Core (Current)**

```bash
terraform apply
```

Creates:
- 12+ enabled GCP APIs
- 2 service accounts (dev + GKE workload)
- IAM role bindings
- 3 Secret Manager secrets (empty, add values manually)

### **Phase 2: Network (Future)**

Uncomment `network.tf` to create:
- VPC network
- Subnets with secondary ranges
- Cloud NAT
- Firewall rules

### **Phase 3: GKE (Future)**

Uncomment `gke.tf` to create:
- GKE cluster with Autopilot or Standard
- Node pools with autoscaling
- Workload Identity configuration

---

## 🔐 Service Accounts

### **platform-dev-sa**
**Purpose**: Local development and CI/CD deployment

**Permissions**:
- GKE management
- Storage access
- Vertex AI access
- Secret Manager admin
- Artifact Registry writer

**Usage**:
```bash
# Create key
gcloud iam service-accounts keys create ~/platform-dev-sa.json \
  --iam-account=platform-dev-sa@platform-dev-20251026-v2.iam.gserviceaccount.com

# Use in .env
export GOOGLE_APPLICATION_CREDENTIALS=~/platform-dev-sa.json
```

### **platform-gke-workload**
**Purpose**: Services running in GKE (Workload Identity)

**Permissions**:
- Read from GCS
- Use Vertex AI
- Read secrets
- Write metrics/logs

**Usage**: Automatically bound to Kubernetes service accounts

---

## 🔒 Adding Secrets

Terraform creates the secret placeholders. Add values manually:

```bash
# Anthropic API Key
echo -n "sk-ant-..." | gcloud secrets versions add anthropic-api-key --data-file=-

# OpenAI API Key
echo -n "sk-..." | gcloud secrets versions add openai-api-key --data-file=-

# Gemini API Key (optional)
echo -n "..." | gcloud secrets versions add gemini-api-key --data-file=-

# Verify
gcloud secrets versions access latest --secret=anthropic-api-key
```

---

## 📊 Outputs

After `terraform apply`, you'll see:

```hcl
Outputs:

project_info = {
  project_id  = "platform-dev-20251026-v2"
  region      = "us-central1"
  environment = "dev"
}

service_accounts = {
  platform_dev = "platform-dev-sa@platform-dev-20251026-v2.iam.gserviceaccount.com"
  gke_workload = "platform-gke-workload@platform-dev-20251026-v2.iam.gserviceaccount.com"
}

next_steps = "..."
```

---

## 🔄 State Management

### **Local State** (Default - for now)

```hcl
# State stored in: terraform.tfstate (gitignored)
```

### **Remote State** (Recommended for team)

Uncomment in `main.tf`:

```hcl
terraform {
  backend "gcs" {
    bucket = "platform-terraform-state"
    prefix = "terraform/state"
  }
}
```

Then:

```bash
# Create state bucket
gsutil mb gs://platform-terraform-state

# Enable versioning
gsutil versioning set on gs://platform-terraform-state

# Migrate state
terraform init -migrate-state
```

---

## 🌍 Multi-Environment Setup

### **Workspaces** (Simple)

```bash
# Create environments
terraform workspace new dev
terraform workspace new staging
terraform workspace new prod

# Switch
terraform workspace select dev
terraform apply
```

### **Separate Directories** (Recommended)

```
infrastructure/terraform/
├── environments/
│   ├── dev/
│   │   ├── main.tf
│   │   └── terraform.tfvars
│   ├── staging/
│   │   ├── main.tf
│   │   └── terraform.tfvars
│   └── prod/
│       ├── main.tf
│       └── terraform.tfvars
└── modules/
    ├── project/
    ├── network/
    └── gke/
```

---

## 🚨 Important Notes

### **Cost Implications**

Current setup costs **~$0** (just API enablement and service accounts)

When you add:
- **GKE Standard**: ~$75/month (3 e2-standard-4 nodes)
- **GKE Autopilot**: Pay per pod (~$30-50/month for small workloads)
- **Cloud Run**: Pay per request (~$5-20/month)
- **Preemptible nodes**: Save 60-80% on GKE

### **Billing Alerts**

Set budget alerts:

```bash
gcloud billing budgets create \
  --billing-account=018DA9-451650-8109DD \
  --display-name="Platform Dev Budget" \
  --budget-amount=100USD \
  --threshold-rule=percent=50 \
  --threshold-rule=percent=90
```

### **Cleanup**

```bash
# Destroy everything
terraform destroy

# Keep project but remove resources
terraform destroy -target=google_container_cluster.platform
```

---

## 🎯 Recommended Workflow

### **Phase 1: Manual Setup** (Done ✅)
- Created project manually
- Enabled initial APIs
- Created service account
- Downloaded key

### **Phase 2: Import to Terraform** (Now)
```bash
# Import existing project resources
terraform import google_project_service.required_apis["container.googleapis.com"] platform-dev-20251026-v2/container.googleapis.com
terraform import google_service_account.platform_dev projects/platform-dev-20251026-v2/serviceAccounts/platform-dev-sa@platform-dev-20251026-v2.iam.gserviceaccount.com

# Then manage with Terraform going forward
```

### **Phase 3: Expand Infrastructure** (Future)
- Add VPC networking
- Add GKE cluster
- Add Cloud Run services
- Add monitoring/logging

---

## 💡 Pro Tips

1. **Always run `terraform plan` first** - See what will change
2. **Use remote state for teams** - Avoid conflicts
3. **Tag everything** - Use labels for cost tracking
4. **Use modules** - Reuse common patterns
5. **Version your modules** - Pin versions in production
6. **Separate environments** - Dev, staging, prod
7. **Automate with CI/CD** - GitHub Actions + Terraform Cloud

---

## 🆘 Troubleshooting

### **"API not enabled"**

```bash
# Enable manually first
gcloud services enable container.googleapis.com

# Then run terraform
terraform apply
```

### **"Permission denied"**

```bash
# Check your auth
gcloud auth application-default login

# Verify service account permissions
gcloud projects get-iam-policy platform-dev-20251026-v2
```

### **"Resource already exists"**

```bash
# Import existing resource
terraform import <resource_type>.<name> <resource_id>
```

---

## 📚 Resources

- [Terraform GCP Provider Docs](https://registry.terraform.io/providers/hashicorp/google/latest/docs)
- [GCP Best Practices](https://cloud.google.com/docs/terraform/best-practices-for-terraform)
- [Terraform Best Practices](https://www.terraform-best-practices.com/)

---

## ✅ Next Steps

1. **Run `terraform init`** - Initialize Terraform
2. **Run `terraform plan`** - Review changes
3. **Run `terraform apply`** - Create infrastructure
4. **Add secret values** - Manually add API keys
5. **Create service account key** - Download for local use
6. **Update .env** - Add GCP credentials

---

**Questions?** Check the [Platform Documentation](../../docs/) or ask the team!
