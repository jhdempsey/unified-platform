# Development Environment Variables

variable "project_id" {
  description = "GCP Project ID for development"
  type        = string
  default     = "platform-dev-20251026-v2"
}

variable "region" {
  description = "Primary GCP region"
  type        = string
  default     = "us-central1"
}

variable "zone" {
  description = "Primary GCP zone"
  type        = string
  default     = "us-central1-a"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "dev"
}

variable "project_labels" {
  description = "Labels for all resources"
  type        = map(string)
  default = {
    platform    = "data-product-platform"
    environment = "dev"
    managed_by  = "terraform"
    team        = "platform-engineering"
  }
}

# Secret Manager
variable "secrets_to_create" {
  description = "Secrets to create in Secret Manager"
  type        = map(string)
  default = {
    anthropic-api-key = "Anthropic Claude API key"
    openai-api-key    = "OpenAI API key"
    gemini-api-key    = "Google Gemini API key"
  }
}

# GKE Configuration (for when you deploy)
variable "vpc_name" {
  description = "VPC network name"
  type        = string
  default     = "platform-network-dev"
}

variable "subnet_cidr" {
  description = "Subnet CIDR range"
  type        = string
  default     = "10.0.0.0/24"
}

variable "gke_cluster_name" {
  description = "GKE cluster name"
  type        = string
  default     = "platform-cluster-dev"
}

variable "gke_node_count" {
  description = "Initial node count"
  type        = number
  default     = 3
}

variable "gke_machine_type" {
  description = "Machine type for nodes"
  type        = string
  default     = "e2-standard-4"
}

variable "gke_preemptible" {
  description = "Use preemptible nodes"
  type        = bool
  default     = true
}
