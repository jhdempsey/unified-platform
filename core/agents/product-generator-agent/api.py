"""
Product Generator API
REST API wrapper for the Product Generator Agent
"""

import os
from typing import Optional, Dict, Any
from datetime import datetime

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from main import ProductGeneratorAgent


# Pydantic models
class ProductRequest(BaseModel):
    """Request to create a new data product"""
    product_name: str = Field(..., min_length=1, max_length=200)
    owner: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., min_length=10)
    additional_context: Optional[Dict[str, Any]] = None
    auto_provision: bool = Field(default=True, description="Automatically provision infrastructure")


class RefineRequest(BaseModel):
    """Request to refine an existing product"""
    product_spec: Dict[str, Any]
    feedback: str = Field(..., min_length=1)


class GenerationResponse(BaseModel):
    """Response from product generation"""
    success: bool
    product_name: str
    owner: str
    product_spec: Optional[Dict[str, Any]] = None
    provisioning: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# Create FastAPI app
app = FastAPI(
    title="Product Generator API",
    description="AI-powered data product creation from natural language",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize agent
agent = None


@app.on_event("startup")
async def startup_event():
    """Initialize agent on startup"""
    global agent
    
    print("🚀 Starting Product Generator API...")
    
    try:
        agent = ProductGeneratorAgent()
        print("✅ Product Generator API ready")
    except Exception as e:
        print(f"❌ Failed to initialize: {e}")
        raise


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint"""
    return {
        "service": "Product Generator API",
        "version": "1.0.0",
        "description": "AI-powered data product creation",
        "endpoints": {
            "POST /generate": "Generate a new data product",
            "POST /refine": "Refine an existing product spec",
            "GET /health": "Health check"
        }
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check"""
    return {
        "status": "healthy",
        "agent_initialized": agent is not None,
        "timestamp": datetime.utcnow().isoformat()
    }


@app.post(
    "/generate",
    response_model=GenerationResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Generation"]
)
async def generate_product(request: ProductRequest):
    """
    Generate a new data product from natural language description
    
    The AI will:
    - Design an Avro schema
    - Recommend Kafka configuration
    - Suggest quality rules
    - Provision infrastructure (if auto_provision=True)
    
    Example request:
    ```json
    {
      "product_name": "Supplier Performance Metrics",
      "owner": "procurement-team",
      "description": "Daily metrics tracking supplier on-time delivery, quality scores, and compliance status",
      "additional_context": {
        "update_frequency": "daily",
        "consumers": ["procurement", "quality-assurance"]
      },
      "auto_provision": true
    }
    ```
    """
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Agent not initialized"
        )
    
    try:
        result = agent.create_product_from_request(
            description=request.description,
            product_name=request.product_name,
            owner=request.owner,
            additional_context=request.additional_context,
            auto_provision=request.auto_provision
        )
        
        return GenerationResponse(**result)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Generation failed: {str(e)}"
        )


@app.post("/refine", tags=["Generation"])
async def refine_product(request: RefineRequest):
    """
    Refine an existing product specification based on feedback
    
    Example request:
    ```json
    {
      "product_spec": { ... previous spec ... },
      "feedback": "Add a field for supplier contact email and increase retention to 30 days"
    }
    ```
    """
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Agent not initialized"
        )
    
    try:
        refined_spec = agent.refine_product(
            product_spec=request.product_spec,
            feedback=request.feedback
        )
        
        return {
            "success": True,
            "product_spec": refined_spec,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Refinement failed: {str(e)}"
        )


@app.get("/examples", tags=["Documentation"])
async def get_examples():
    """Get example requests"""
    return {
        "examples": [
            {
                "name": "Supplier Performance Metrics",
                "request": {
                    "product_name": "Supplier Performance Metrics",
                    "owner": "procurement-team",
                    "description": "Track supplier performance including on-time delivery rate, quality scores, and compliance status. Updates daily.",
                    "additional_context": {
                        "update_frequency": "daily",
                        "consumers": ["procurement", "quality-assurance", "finance"]
                    }
                }
            },
            {
                "name": "Real-time Order Stream",
                "request": {
                    "product_name": "Order Stream",
                    "owner": "supply-chain-team",
                    "description": "Real-time stream of order events including placements, confirmations, shipments, and deliveries. Need sub-second latency.",
                    "additional_context": {
                        "latency_requirement": "< 1 second",
                        "volume": "10k orders/day"
                    }
                }
            },
            {
                "name": "Customer Sentiment Analysis",
                "request": {
                    "product_name": "Customer Sentiment Dashboard",
                    "owner": "customer-success-team",
                    "description": "Aggregate customer feedback sentiment scores from reviews, support tickets, and surveys. Weekly rollups with trend analysis.",
                    "additional_context": {
                        "sources": ["zendesk", "trustpilot", "internal_surveys"],
                        "granularity": "weekly"
                    }
                }
            }
        ]
    }


if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", 8003))
    
    print(f"🚀 Starting Product Generator API on port {port}")
    print(f"📖 API docs: http://localhost:{port}/docs")
    
    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=port,
        reload=True
    )
