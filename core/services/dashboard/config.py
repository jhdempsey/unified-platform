"""
Dashboard Configuration
Centralized configuration for Streamlit dashboard
"""
import os

# Environment detection
ENVIRONMENT = os.getenv("ENVIRONMENT", "production")

# =============================================================================
# Cloud Run Service URLs
# =============================================================================

# Base URL pattern for Cloud Run services
CLOUD_RUN_BASE = "https://{service}-742330383495.us-central1.run.app"

# Service URLs
DISCOVERY_AGENT_URL = os.getenv(
    "DISCOVERY_AGENT_URL",
    CLOUD_RUN_BASE.format(service="discovery-agent")
)

AI_GATEWAY_URL = os.getenv(
    "AI_GATEWAY_URL",
    CLOUD_RUN_BASE.format(service="ai-gateway")
)

RAG_SERVICE_URL = os.getenv(
    "RAG_SERVICE_URL",
    CLOUD_RUN_BASE.format(service="rag-service")
)

PRODUCT_SERVICE_URL = os.getenv(
    "PRODUCT_SERVICE_URL",
    CLOUD_RUN_BASE.format(service="product-service")
)

PRODUCT_GENERATOR_URL = os.getenv(
    "PRODUCT_GENERATOR_URL",
    CLOUD_RUN_BASE.format(service="product-generator")
)

ML_CONSUMER_URL = os.getenv(
    "ML_CONSUMER_URL",
    CLOUD_RUN_BASE.format(service="ml-consumer")
)

STREAM_ANALYSIS_URL = os.getenv(
    "STREAM_ANALYSIS_URL",
    CLOUD_RUN_BASE.format(service="stream-analysis")
)

EVENT_PRODUCER_URL = os.getenv(
    "EVENT_PRODUCER_URL",
    CLOUD_RUN_BASE.format(service="event-producer")
)

MCP_SERVER_URL = os.getenv(
    "MCP_SERVER_URL",
    CLOUD_RUN_BASE.format(service="mcp-server")
)

BACKSTAGE_URL = os.getenv(
    "BACKSTAGE_URL",
    CLOUD_RUN_BASE.format(service="backstage")
)

# MLflow - Not currently deployed as Cloud Run service
# Set to empty to indicate unavailable
MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", "")
MLFLOW_UI_URL = os.getenv("MLFLOW_UI_URL", "")

# Kafka UI - Using Confluent Cloud Console
KAFKA_UI_URL = "https://confluent.cloud"

# Prometheus - Not deployed (using Cloud Monitoring instead)
PROMETHEUS_UI_URL = ""

# =============================================================================
# UI URLs for browser links
# =============================================================================

if ENVIRONMENT == "dev":
    # Local development - use localhost
    MLFLOW_UI_URL = "http://localhost:5001"
    DISCOVERY_AGENT_UI_URL = "http://localhost:8004"
    AI_GATEWAY_UI_URL = "http://localhost:8002"
    RAG_SERVICE_UI_URL = "http://localhost:8005"
    PRODUCT_SERVICE_UI_URL = "http://localhost:8001"
    KAFKA_UI_URL = "http://localhost:8080"
else:
    # Production - use Cloud Run URLs
    MLFLOW_UI_URL = MLFLOW_UI_URL or ""  # Not available
    DISCOVERY_AGENT_UI_URL = DISCOVERY_AGENT_URL
    AI_GATEWAY_UI_URL = AI_GATEWAY_URL
    RAG_SERVICE_UI_URL = RAG_SERVICE_URL
    PRODUCT_SERVICE_UI_URL = PRODUCT_SERVICE_URL


# =============================================================================
# API Endpoints for internal calls
# =============================================================================

def get_service_endpoints():
    """Get all service endpoints for health checks and API calls"""
    return {
        "internal": {
            "discovery_agent": DISCOVERY_AGENT_URL,
            "ai_gateway": AI_GATEWAY_URL,
            "rag_service": RAG_SERVICE_URL,
            "product_service": PRODUCT_SERVICE_URL,
            "product_generator": PRODUCT_GENERATOR_URL,
            "ml_consumer": ML_CONSUMER_URL,
            "stream_analysis": STREAM_ANALYSIS_URL,
            "event_producer": EVENT_PRODUCER_URL,
            "mcp_server": MCP_SERVER_URL,
        },
        "ui": {
            "discovery_agent": DISCOVERY_AGENT_UI_URL,
            "ai_gateway": AI_GATEWAY_UI_URL,
            "rag_service": RAG_SERVICE_UI_URL,
            "product_service": PRODUCT_SERVICE_UI_URL,
            "kafka": KAFKA_UI_URL,
            "backstage": BACKSTAGE_URL,
            "mlflow": MLFLOW_UI_URL,
        }
    }


# =============================================================================
# Feature Flags
# =============================================================================

FEATURES = {
    "mlflow_enabled": bool(MLFLOW_TRACKING_URI),
    "prometheus_enabled": bool(PROMETHEUS_UI_URL),
    "kafka_metrics_enabled": True,
}


if __name__ == "__main__":
    print(f"Environment: {ENVIRONMENT}")
    print(f"\nService Endpoints:")
    endpoints = get_service_endpoints()
    for category, services in endpoints.items():
        print(f"\n  {category}:")
        for name, url in services.items():
            status = "✅" if url else "❌"
            print(f"    {status} {name}: {url or 'Not configured'}")
