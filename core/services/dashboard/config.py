"""
Dashboard configuration - Environment-aware service URLs
Separates internal (container-to-container) and external (browser) URLs
"""
import os

# Determine environment
ENVIRONMENT = os.getenv("ENVIRONMENT", "dev")
VERTICAL = os.getenv("VERTICAL", "supply-chain")

# ============================================================================
# INTERNAL URLs (for server-side API calls from dashboard container)
# ============================================================================
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
SCHEMA_REGISTRY_URL = os.getenv("SCHEMA_REGISTRY_URL", "http://schema-registry:8081")
MLFLOW_TRACKING_URI = "http://mlflow:5000"  # Internal container port
MODEL_INFERENCE_URL = "http://model-inference:8001"
RAG_SERVICE_URL = "http://rag-service:8005"
PROMETHEUS_URL = "http://prometheus:9090"  # Internal container port
DISCOVERY_AGENT_URL = "http://discovery-agent:8004"

# ============================================================================
# EXTERNAL URLs (for browser links and client-side calls)
# ============================================================================
if ENVIRONMENT == "dev":
    # Local Docker - use localhost with host-mapped ports
    MLFLOW_UI_URL = "http://localhost:5001"
    MODEL_INFERENCE_UI_URL = "http://localhost:8001"
    RAG_SERVICE_UI_URL = "http://localhost:8005"
    PROMETHEUS_UI_URL = "http://localhost:9091"
    DISCOVERY_AGENT_UI_URL = "http://localhost:8004"
    AI_GATEWAY_UI_URL = "http://localhost:8002"
    KAFKA_UI_URL = "http://localhost:8080"
else:
    # GCP/Production - use external URLs from environment
    MLFLOW_UI_URL = os.getenv("MLFLOW_UI_URL", MLFLOW_TRACKING_URI)
    MODEL_INFERENCE_UI_URL = os.getenv("MODEL_INFERENCE_UI_URL", MODEL_INFERENCE_URL)
    RAG_SERVICE_UI_URL = os.getenv("RAG_SERVICE_UI_URL", RAG_SERVICE_URL)
    PROMETHEUS_UI_URL = os.getenv("PROMETHEUS_UI_URL", PROMETHEUS_URL)
    DISCOVERY_AGENT_UI_URL = os.getenv("DISCOVERY_AGENT_UI_URL", DISCOVERY_AGENT_URL)
    AI_GATEWAY_UI_URL = os.getenv("AI_GATEWAY_UI_URL", "http://ai-gateway:8002")
    KAFKA_UI_URL = os.getenv("KAFKA_UI_URL", "http://kafka-ui:8080")

# Connection settings
REQUEST_TIMEOUT = 10
KAFKA_CONSUMER_TIMEOUT = 2000

def show_config():
    """Return configuration for debugging"""
    return {
        "environment": ENVIRONMENT,
        "vertical": VERTICAL,
        "internal_urls": {
            "mlflow": MLFLOW_TRACKING_URI,
            "model_inference": MODEL_INFERENCE_URL,
            "rag": RAG_SERVICE_URL,
            "prometheus": PROMETHEUS_URL,
        },
        "external_urls": {
            "mlflow_ui": MLFLOW_UI_URL,
            "model_inference_ui": MODEL_INFERENCE_UI_URL,
            "rag_ui": RAG_SERVICE_UI_URL,
            "prometheus_ui": PROMETHEUS_UI_URL,
        }
    }
