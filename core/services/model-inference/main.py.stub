"""
Model Inference Service
Serves ML models via REST API
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os

app = FastAPI(title="Model Inference Service")

# Note: ML models are mounted from templates/{vertical}/models
# For now, provide a health endpoint and stub predict endpoint

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "model-inference"}

@app.post("/predict/{model_name}")
async def predict(model_name: str, data: dict):
    """
    Predict endpoint - will load models dynamically from vertical templates
    """
    return {
        "model": model_name,
        "status": "stub",
        "message": "Model inference will be implemented per vertical"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
