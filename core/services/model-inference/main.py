"""
Enhanced Model Inference Service - Serves multiple ML models
Supports both legacy (numpy) and new (scikit-learn) models
"""

import os
import sys
from pathlib import Path
from typing import Any, Dict, List

import mlflow
from fastapi import BackgroundTasks, FastAPI, HTTPException
from pydantic import BaseModel, Field

# Add paths for vertical models
VERTICAL = os.getenv("VERTICAL", "supply-chain")
vertical_models_path = Path(f"/app/vertical-models")
if vertical_models_path.exists():
    sys.path.insert(0, str(vertical_models_path))

# Import models from vertical
try:
    from demand_forecasting.model import DemandForecastingModel
    from demand_forecasting.rf_model import SupplyChainRFModel
    from inventory_optimization.model import InventoryOptimizationModel
    from supplier_reliability.model import SupplierReliabilityModel
    MODELS_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  Could not import models: {e}")
    MODELS_AVAILABLE = False
    DemandForecastingModel = None
    SupplyChainRFModel = None
    InventoryOptimizationModel = None
    SupplierReliabilityModel = None
app = FastAPI(
    title="Model Inference Service",
    version="2.0.0",
    description="Multi-model inference service with MLflow integration",
)

# Model registry - supports multiple models and versions
models: Dict[str, Any] = {}
model_metadata: Dict[str, Dict[str, Any]] = {}


def load_models():
    """Load all available models on startup"""
    print("🔄 Loading models...")

    # Load legacy numpy-based model (backward compatibility)
    try:
        models["demand_forecasting_legacy"] = DemandForecastingModel()
        model_metadata["demand_forecasting_legacy"] = {
            "type": "time_series",
            "version": "1.0.0",
            "framework": "numpy",
            "description": "Legacy demand forecasting model",
            "status": "active",
        }
        print("✅ Loaded: demand_forecasting_legacy (numpy)")
    except Exception as e:
        print(f"⚠️  Failed to load legacy model: {e}")

    # Load Random Forest model
    try:
        rf_model = SupplyChainRFModel()

        # Try loading from local backup first (faster)
        local_path = "/app/models/rf_model.joblib"
        if os.path.exists(local_path):
            rf_model.load_local(local_path)
            print("✅ Loaded: supply_chain_rf from local backup")
        else:
            # Train on startup if no saved model
            print("📊 No saved model found, training new model...")
            rf_model.train(n_estimators=100, max_depth=10, log_to_mlflow=True)
            rf_model.save_local(local_path)
            print("✅ Trained and saved: supply_chain_rf")

        models["supply_chain_rf"] = rf_model
        model_metadata["supply_chain_rf"] = {
            "type": "regression",
            "version": "2.0.0",
            "framework": "scikit-learn",
            "description": "Random Forest model for fulfillment time prediction",
            "status": "active",
            "mlflow_integrated": True,
        }

    except Exception as e:
        print(f"⚠️  Failed to load RF model: {e}")
        import traceback

        traceback.print_exc()

    
    # Load Inventory Optimization model
    try:
        if InventoryOptimizationModel:
            models["inventory_optimization"] = InventoryOptimizationModel()
            model_metadata["inventory_optimization"] = {
                "type": "optimization",
                "version": "1.0.0",
                "framework": "numpy",
                "description": "Inventory optimization model",
                "status": "active",
            }
            print("✅ Loaded: inventory_optimization")
    except Exception as e:
        print(f"⚠️  Failed to load inventory model: {e}")

    # Load Supplier Reliability model
    try:
        if SupplierReliabilityModel:
            models["supplier_reliability"] = SupplierReliabilityModel()
            model_metadata["supplier_reliability"] = {
                "type": "scoring",
                "version": "1.0.0",
                "framework": "numpy",
                "description": "Supplier reliability scoring model",
                "status": "active",
            }
            print("✅ Loaded: supplier_reliability")
    except Exception as e:
        print(f"⚠️  Failed to load supplier model: {e}")

    print(f"✅ Loaded {len(models)} models")


@app.on_event("startup")
async def startup_event():
    """Initialize models on startup"""
    load_models()


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================


class PredictionRequest(BaseModel):
    """Legacy prediction request format (backward compatible)"""

    tenant_id: str
    model_name: str
    features: dict


class DemandPredictionRequest(BaseModel):
    """Request for supply chain RF model"""

    product_category: int = Field(
        ..., ge=0, le=4, description="0=Dairy, 1=Produce, 2=Meat, 3=Bakery, 4=Frozen"
    )
    order_quantity: int = Field(..., ge=10, le=1000)
    warehouse_distance: float = Field(..., ge=5.0, le=500.0)
    day_of_week: int = Field(..., ge=0, le=6)
    season: int = Field(
        ..., ge=0, le=3, description="0=Winter, 1=Spring, 2=Summer, 3=Fall"
    )
    supplier_reliability: float = Field(..., ge=60.0, le=100.0)
    weather_condition: int = Field(
        ..., ge=0, le=2, description="0=Clear, 1=Rain, 2=Snow"
    )


class TrainingRequest(BaseModel):
    """Request to trigger model training"""

    model_name: str = "supply_chain_rf"
    n_estimators: int = Field(default=100, ge=10, le=500)
    max_depth: int = Field(default=10, ge=3, le=30)
    log_to_mlflow: bool = True


# ============================================================================
# ENDPOINTS
# ============================================================================


@app.get("/")
async def root():
    """Root endpoint with service info"""
    return {
        "service": "Model Inference Service",
        "version": "2.0.0",
        "available_models": list(models.keys()),
        "model_count": len(models),
        "features": [
            "Multi-model support",
            "MLflow integration",
            "On-demand training",
            "Backward compatible",
            "Batch predictions",
        ],
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "model-inference",
        "version": "2.0.0",
        "models_loaded": len(models),
        "available_models": list(models.keys()),
    }


@app.get("/models")
async def list_models():
    """List all available models with metadata"""
    return {"models": model_metadata, "count": len(models)}


@app.get("/models/{model_name}/info")
async def get_model_info(model_name: str):
    """Get detailed information about a specific model"""
    if model_name not in models:
        raise HTTPException(status_code=404, detail=f"Model '{model_name}' not found")

    model = models[model_name]

    # Get model-specific info
    if hasattr(model, "get_info"):
        model_info = model.get_info()
    else:
        model_info = {
            "model_name": model_name,
            "version": getattr(model, "version", "unknown"),
        }

    return {**model_info, "metadata": model_metadata.get(model_name, {})}


@app.post("/predict")
async def predict(request: PredictionRequest):
    """
    Legacy prediction endpoint (backward compatible)
    Supports the original demand_forecasting model
    """
    if request.model_name not in models:
        raise HTTPException(
            status_code=404,
            detail=f"Model '{request.model_name}' not found. Available: {list(models.keys())}",  # noqa: E501
        )

    try:
        model = models[request.model_name]
        prediction = model.predict(request.features)

        return {
            "tenant_id": request.tenant_id,
            "model_name": request.model_name,
            "prediction": prediction,
            "status": "success",
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Prediction failed: {str(e)}"
        ) from e


@app.post("/predict/demand")
async def predict_demand(request: DemandPredictionRequest):
    """
    Predict order fulfillment time using Random Forest model
    This is the new scikit-learn model endpoint
    """
    model_name = "supply_chain_rf"

    if model_name not in models:
        raise HTTPException(status_code=503, detail="Supply chain RF model not loaded")

    try:
        model = models[model_name]

        features = {
            "product_category": request.product_category,
            "order_quantity": request.order_quantity,
            "warehouse_distance": request.warehouse_distance,
            "day_of_week": request.day_of_week,
            "season": request.season,
            "supplier_reliability": request.supplier_reliability,
            "weather_condition": request.weather_condition,
        }

        prediction = model.predict(features)

        return {"status": "success", "model_name": model_name, **prediction}

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Prediction failed: {str(e)}"
        ) from e


@app.post("/predict/demand/batch")
async def predict_demand_batch(requests: List[DemandPredictionRequest]):
    """
    Batch prediction endpoint for multiple orders
    Processes multiple predictions in a single request
    """
    model_name = "supply_chain_rf"

    if model_name not in models:
        raise HTTPException(status_code=503, detail="Supply chain RF model not loaded")

    if not requests:
        raise HTTPException(status_code=400, detail="Empty request list")

    try:
        model = models[model_name]
        predictions = []

        for idx, req in enumerate(requests):
            features = {
                "product_category": req.product_category,
                "order_quantity": req.order_quantity,
                "warehouse_distance": req.warehouse_distance,
                "day_of_week": req.day_of_week,
                "season": req.season,
                "supplier_reliability": req.supplier_reliability,
                "weather_condition": req.weather_condition,
            }

            prediction = model.predict(features)
            predictions.append({"order_id": idx, **prediction})

        return {
            "status": "success",
            "model_name": model_name,
            "count": len(predictions),
            "predictions": predictions,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Batch prediction failed: {str(e)}"
        ) from e


@app.post("/train/{model_name}")
async def train_model(
    model_name: str, request: TrainingRequest, background_tasks: BackgroundTasks
):
    """
    Trigger model training (can be run in background)
    """
    if model_name != "supply_chain_rf":
        raise HTTPException(
            status_code=400, detail="Only 'supply_chain_rf' supports on-demand training"
        )

    def _train():
        try:
            print(f"🚀 Starting training for {model_name}...")

            # CRITICAL FIX: Set MLflow experiment BEFORE creating model instance
            if request.log_to_mlflow:
                import os

                mlflow_uri = os.getenv(
                    "MLFLOW_TRACKING_URI",
                    "http://mlflow.default.svc.cluster.local:5000",
                )
                mlflow.set_tracking_uri(mlflow_uri)
                mlflow.set_experiment("supply-chain.predictions")  # ✅ With dots!
                print("🔗 MLflow experiment set: supply-chain.predictions")

            model = SupplyChainRFModel()
            model.train(
                n_estimators=request.n_estimators,
                max_depth=request.max_depth,
                log_to_mlflow=request.log_to_mlflow,
            )

            # Update loaded model
            models[model_name] = model

            # Save backup
            model.save_local("/app/models/rf_model.joblib")

            print(f"✅ Training complete for {model_name}")

        except Exception as e:
            print(f"❌ Training failed: {e}")
            import traceback

            traceback.print_exc()

    # Run training in background
    background_tasks.add_task(_train)

    return {
        "status": "training_started",
        "model_name": model_name,
        "message": "Training started in background. Check logs for progress.",
    }


@app.post("/reload")
async def reload_models():
    """Reload all models (useful after training)"""
    try:
        load_models()
        return {
            "status": "success",
            "message": "Models reloaded",
            "models_loaded": len(models),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Reload failed: {str(e)}") from e


# ============================================================================
# ERROR HANDLERS
# ============================================================================


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global error handler"""
    return {"status": "error", "message": str(exc), "type": type(exc).__name__}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)
