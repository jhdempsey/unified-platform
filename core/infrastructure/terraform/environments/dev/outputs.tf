# Development Environment Outputs

output "project_info" {
  value = {
    project_id  = var.project_id
    region      = var.region
    zone        = var.zone
    environment = var.environment
  }
  description = "Project configuration"
}

output "service_accounts" {
  value = {
    platform_dev = module.project.platform_dev_service_account.email
    gke_workload = module.project.gke_workload_service_account.email
  }
  description = "Service account emails"
}

output "secrets" {
  value       = module.secrets.secrets_created
  description = "Created secrets (add values manually)"
}

output "next_steps" {
  value = <<-EOT
    ✅ Development infrastructure provisioned!
    
    📝 Next steps:
    
    1. Create service account key:
       gcloud iam service-accounts keys create ~/platform-dev-sa.json \
         --iam-account=${module.project.platform_dev_service_account.email}
    
    2. Add secret values:
       echo -n "YOUR_KEY" | gcloud secrets versions add anthropic-api-key --data-file=-
       echo -n "YOUR_KEY" | gcloud secrets versions add openai-api-key --data-file=-
    
    3. Update .env:
       export GOOGLE_APPLICATION_CREDENTIALS=~/platform-dev-sa.json
       export GCP_PROJECT_ID=${var.project_id}
    
    4. When ready to deploy GKE, uncomment network and gke modules in main.tf
  EOT
  description = "Post-provisioning steps"
}
