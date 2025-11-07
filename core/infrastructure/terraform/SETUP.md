# Terraform Setup - Quick Start

## ✅ **Yes, Use `environments/dev/`!**

Your Terraform is now organized with proper multi-environment structure.

## 📁 **Directory Structure**

```
infrastructure/terraform/
├── environments/
│   ├── dev/          ← YOUR WORKING DIRECTORY
│   ├── staging/      ← For future staging environment
│   └── prod/         ← For future production environment
└── modules/
    ├── project/      ← Reusable module for project setup
    ├── secrets/      ← Reusable module for Secret Manager
    ├── network/      ← TODO: VPC module
    └── gke/          ← TODO: GKE module
```

---

## 🚀 **Setup Steps**

### **1. Fix Quota Project Warning**

```bash
gcloud auth application-default set-quota-project platform-dev-20251026-v2
```

### **2. Navigate to Dev Environment**

```bash
cd infrastructure/terraform/environments/dev
```

### **3. Create terraform.tfvars** (Optional)

```bash
cat > terraform.tfvars << EOF
project_id = "platform-dev-20251026-v2"
region     = "us-central1"
zone       = "us-central1-a"
EOF
```

**Note**: `terraform.tfvars` is gitignored, so your values stay private.

### **4. Initialize Terraform**

```bash
terraform init
```

### **5. Review Changes**

```bash
terraform plan
```

You should see it will create:
- ~12 API enablements
- 2 service accounts
- ~15 IAM role bindings
- 3 Secret Manager secrets

### **6. Apply (Create Resources)**

```bash
terraform apply
```

Type `yes` when prompted.

---

## 📝 **After Terraform Apply**

### **1. Create Service Account Key**

```bash
gcloud iam service-accounts keys create ~/.config/gcloud/platform-dev-sa.json \
  --iam-account=platform-dev-sa@platform-dev-20251026-v2.iam.gserviceaccount.com
```

### **2. Add Secret Values**

```bash
# Add your API keys
echo -n "YOUR_ANTHROPIC_KEY" | gcloud secrets versions add anthropic-api-key --data-file=-
echo -n "YOUR_OPENAI_KEY" | gcloud secrets versions add openai-api-key --data-file=-
```

### **3. Update .env**

```bash
# In your project root .env
GOOGLE_APPLICATION_CREDENTIALS=/Users/jhdempsey/.config/gcloud/platform-dev-sa.json
GCP_PROJECT_ID=platform-dev-20251026-v2
GCP_REGION=us-central1
```

---

## 🎯 **Why This Structure?**

### **Environment Separation**
- **dev/**: Your current work, preemptible nodes, lower cost
- **staging/**: Pre-production testing (future)
- **prod/**: Production deployment (future)

### **Reusable Modules**
- **project/**: Service accounts, IAM, APIs
- **secrets/**: Secret Manager configuration
- **network/**: VPC networking (when you add GKE)
- **gke/**: GKE cluster (when you're ready)

### **Benefits**
- ✅ Clean separation of environments
- ✅ DRY (Don't Repeat Yourself) - modules are reused
- ✅ Easy to add staging/prod later
- ✅ Each environment has its own state
- ✅ Variables scoped per environment

---

## 📊 **What Terraform Manages vs Manual**

### **Terraform Manages**
- ✅ API enablement
- ✅ Service accounts
- ✅ IAM roles
- ✅ Secret Manager (placeholders)
- ⏳ GKE cluster (when you uncomment)
- ⏳ VPC network (when you uncomment)

### **Manual Steps**
- ❌ Project creation (already done)
- ❌ Service account keys (security best practice)
- ❌ Secret values (sensitive data)
- ❌ Your gcloud auth

---

## 🔄 **Adding GKE Later**

When ready to deploy:

```bash
# 1. Edit environments/dev/main.tf
# Uncomment the network module
# Uncomment the gke module

# 2. Apply
terraform apply

# 3. Get cluster credentials
gcloud container clusters get-credentials platform-cluster-dev \
  --region us-central1
```

---

## 🌍 **Adding Staging/Prod**

```bash
# Copy dev environment
cp -r environments/dev environments/staging

# Edit staging/variables.tf
# Change project_id, environment name, etc.

# Initialize and apply
cd environments/staging
terraform init
terraform apply
```

---

## 💡 **Pro Tips**

1. **Always work in environment directory**
   ```bash
   cd environments/dev  # Not root terraform/
   ```

2. **Use terraform.tfvars for overrides**
   ```bash
   # Gitignored, safe for local values
   ```

3. **Check state before changes**
   ```bash
   terraform state list
   ```

4. **Plan before apply**
   ```bash
   terraform plan -out=tfplan
   terraform apply tfplan
   ```

5. **Use workspaces for quick env switching**
   ```bash
   terraform workspace list
   terraform workspace select dev
   ```

---

## ✅ **Your Next Command**

```bash
cd infrastructure/terraform/environments/dev
gcloud auth application-default set-quota-project platform-dev-20251026-v2
terraform init
terraform plan
```

That's it! You're ready to go. 🚀
