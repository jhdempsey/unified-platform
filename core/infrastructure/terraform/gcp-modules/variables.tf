variable "project_id" {
  description = "GCP Project ID"
  type        = string
  default     = ""
}

variable "project_name" {
  description = "Project name prefix"
  type        = string
  default     = "ai-platform"
}

variable "region" {
  description = "GCP Region"
  type        = string
  default     = "us-central1"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "demo"
}

# GKE Configuration
variable "use_autopilot" {
  description = "Use GKE Autopilot (recommended for demo)"
  type        = bool
  default     = true
}

variable "machine_type" {
  description = "GKE node machine type (if not autopilot)"
  type        = string
  default     = "e2-small" # Cost-effective
}

variable "min_nodes" {
  description = "Minimum number of nodes"
  type        = number
  default     = 1
}

variable "max_nodes" {
  description = "Maximum number of nodes"
  type        = number
  default     = 3
}

variable "use_preemptible" {
  description = "Use preemptible nodes for cost savings"
  type        = bool
  default     = true
}

# Cloud Run Configuration
variable "ai_gateway_image" {
  description = "AI Gateway container image"
  type        = string
  default     = "gcr.io/PROJECT_ID/ai-gateway:latest"
}

variable "max_cloud_run_instances" {
  description = "Max Cloud Run instances"
  type        = number
  default     = 10
}

variable "allow_unauthenticated" {
  description = "Allow unauthenticated access to Cloud Run services"
  type        = bool
  default     = false # Set to true for demo only
}

# Redis Configuration
variable "redis_tier" {
  description = "Redis tier (BASIC or STANDARD_HA)"
  type        = string
  default     = "BASIC" # Cost-effective for demo
}

variable "redis_memory_gb" {
  description = "Redis memory in GB"
  type        = number
  default     = 1 # Minimum
}

# API Keys (optional - use Secret Manager)
variable "gemini_api_key" {
  description = "Gemini API Key"
  type        = string
  default     = ""
  sensitive   = true
}

variable "openai_api_key" {
  description = "OpenAI API Key"
  type        = string
  default     = ""
  sensitive   = true
}

variable "anthropic_api_key" {
  description = "Anthropic API Key"
  type        = string
  default     = ""
  sensitive   = true
}

variable "enable_mlflow" {
  description = "Enable MLflow deployment"
  type        = bool
  default     = true
}

variable "mlflow_db_tier" {
  description = "Cloud SQL tier for MLflow"
  type        = string
  default     = "db-f1-micro"
}
