# ==============================================================================
# VERTEX AI AGENT BUILDER - Supply Chain Assistant
# ==============================================================================
# Creates Agent Builder data store and agent engine with MCP server integration

# Data Store for Agent Builder
resource "google_discovery_engine_data_store" "supply_chain_docs" {
  location                    = "global"
  data_store_id               = "supply-chain-docs"
  display_name                = "Supply Chain Documentation"
  industry_vertical           = "GENERIC"
  content_config              = "NO_CONTENT"  # Using external tools only
  solution_types              = ["SOLUTION_TYPE_CHAT"]
  create_advanced_site_search = false

  project = var.project_id
}

# Chat Engine (Agent)
resource "google_discovery_engine_chat_engine" "supply_chain_assistant" {
  engine_id      = "supply-chain-assistant"
  collection_id  = "default_collection"
  location       = google_discovery_engine_data_store.supply_chain_docs.location
  display_name   = "Supply Chain Assistant"
  industry_vertical = "GENERIC"

  data_store_ids = [
    google_discovery_engine_data_store.supply_chain_docs.data_store_id
  ]

  chat_engine_config {
    agent_creation_config {
      business             = "Supply Chain Operations"
      default_language_code = "en"
      time_zone            = "America/Los_Angeles"
    }
  }

  common_config {
    company_name = "iTradeNetwork"
  }

  project = var.project_id
}

# Outputs
output "agent_builder_data_store_id" {
  value       = google_discovery_engine_data_store.supply_chain_docs.data_store_id
  description = "Agent Builder data store ID"
}

output "agent_builder_engine_id" {
  value       = google_discovery_engine_chat_engine.supply_chain_assistant.engine_id
  description = "Agent Builder chat engine ID"
}

output "agent_builder_console_url" {
  value       = "https://console.cloud.google.com/gen-app-builder/engines/${google_discovery_engine_chat_engine.supply_chain_assistant.engine_id}/edit?project=${var.project_id}"
  description = "Console URL to configure agent tools"
}

output "agent_builder_tool_config_instructions" {
  value = <<-EOT

  ⚠️  Manual Tool Configuration Required:

  1. Go to: ${google_discovery_engine_chat_engine.supply_chain_assistant.name}
  2. Navigate to 'Tools' tab
  3. Add OpenAPI tool:
     - Name: Query Documentation
     - OpenAPI Spec: ${google_cloud_run_service.mcp_server.status[0].url}/openapi.json
     - Authentication: None

  4. Add system instructions:
     You are a Supply Chain Assistant. Use query_documentation tool
     to search company policies when users ask about supplier requirements,
     quality standards, or compliance procedures.

  EOT
  description = "Instructions for manual tool configuration"
}
