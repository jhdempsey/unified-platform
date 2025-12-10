"""
Vertical-specific configurations
Makes it easy to support multiple industries with the same dashboard
"""

VERTICAL_CONFIG = {
    "supply-chain": {
        "name": "Supply Chain Analytics",
        "icon": "🚚",
        "description": "Perishable Food Supply Chain Management",
        "color": "#2E7D32",
        "metrics": {
            "primary": ["Orders Processed", "Cold Chain Compliance", "Supplier Quality"],
            "secondary": ["Inventory Turnover", "Delivery Performance", "Waste Reduction"]
        },
        "topics": [
            "supply-chain.orders",
            "supply-chain.shipments", 
            "supply-chain.quality-alerts",
            "supply-chain.suppliers",
            "supply-chain.inventory"
        ],
        "models": {
            "demand-forecasting": "Predict product demand based on historical patterns",
            "inventory-optimization": "Optimize stock levels to minimize waste",
            "supplier-reliability": "Score and rank supplier performance"
        },
        "rag_examples": [
            "What are the cold chain requirements for perishable goods?",
            "How should we handle temperature excursions?",
            "What are optimal reorder points for seasonal items?",
            "What are food safety compliance requirements?"
        ],
        "kpis": [
            {"name": "Cold Chain Compliance", "unit": "%", "target": 99.5},
            {"name": "On-Time Delivery", "unit": "%", "target": 95.0},
            {"name": "Waste Reduction", "unit": "%", "target": 15.0}
        ]
    },
    "retail": {
        "name": "Retail Analytics",
        "icon": "🛍️",
        "description": "Omnichannel Retail Operations",
        "color": "#1976D2",
        "metrics": {
            "primary": ["Sales Volume", "Customer Satisfaction", "Inventory Health"],
            "secondary": ["Conversion Rate", "Average Basket Size", "Return Rate"]
        },
        "topics": [
            "retail.transactions",
            "retail.inventory",
            "retail.customer-events",
            "retail.promotions"
        ],
        "models": {
            "sales-forecasting": "Predict sales trends and seasonality",
            "recommendation-engine": "Personalized product recommendations",
            "churn-prediction": "Identify at-risk customers"
        },
        "rag_examples": [
            "What are the return policies?",
            "How to handle promotional campaigns?",
            "What are inventory management best practices?",
            "How to improve customer satisfaction?"
        ],
        "kpis": [
            {"name": "Conversion Rate", "unit": "%", "target": 3.5},
            {"name": "Customer Satisfaction", "unit": "/5", "target": 4.5},
            {"name": "Inventory Turnover", "unit": "x/year", "target": 8.0}
        ]
    },
    "financial-services": {
        "name": "Financial Services",
        "icon": "💰",
        "description": "Real-time Financial Operations & Compliance",
        "color": "#C62828",
        "metrics": {
            "primary": ["Transaction Volume", "Fraud Detection Rate", "Compliance Score"],
            "secondary": ["Processing Time", "Alert Accuracy", "SLA Compliance"]
        },
        "topics": [
            "financial.transactions",
            "financial.fraud-alerts",
            "financial.compliance-events",
            "financial.customer-kyc"
        ],
        "models": {
            "fraud-detection": "Real-time fraud scoring and detection",
            "risk-assessment": "Credit risk and exposure analysis",
            "compliance-monitoring": "Regulatory compliance automation"
        },
        "rag_examples": [
            "What are KYC requirements?",
            "How to detect fraud patterns?",
            "What are AML compliance rules?",
            "What are transaction monitoring thresholds?"
        ],
        "kpis": [
            {"name": "Fraud Detection Rate", "unit": "%", "target": 99.9},
            {"name": "False Positive Rate", "unit": "%", "target": 0.5},
            {"name": "Compliance Score", "unit": "%", "target": 100.0}
        ]
    }
}

def get_vertical_config(vertical: str):
    """Get configuration for specified vertical"""
    return VERTICAL_CONFIG.get(vertical, VERTICAL_CONFIG["supply-chain"])

def get_vertical_name(vertical: str):
    """Get display name for vertical"""
    return get_vertical_config(vertical)["name"]

def get_vertical_icon(vertical: str):
    """Get icon for vertical"""
    return get_vertical_config(vertical)["icon"]

def get_vertical_description(vertical: str):
    """Get description for vertical"""
    return get_vertical_config(vertical)["description"]

def get_vertical_topics(vertical: str):
    """Get expected topics for vertical"""
    return get_vertical_config(vertical)["topics"]

def get_vertical_models(vertical: str):
    """Get models for vertical"""
    return get_vertical_config(vertical)["models"]

def get_rag_examples(vertical: str):
    """Get RAG query examples for vertical"""
    return get_vertical_config(vertical)["rag_examples"]

def get_vertical_kpis(vertical: str):
    """Get KPIs for vertical"""
    return get_vertical_config(vertical)["kpis"]

def list_available_verticals():
    """List all available verticals"""
    return list(VERTICAL_CONFIG.keys())
