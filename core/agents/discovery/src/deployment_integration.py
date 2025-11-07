"""
Deployment Integration for Discovery Agent

Add this to your catalog_api.py to enable product deployment.
Works with your existing recommendations_store (in-memory dict).

Usage:
1. Import at top of catalog_api.py:
   from deployment_integration import setup_deployment_endpoints
   
2. After creating your FastAPI app:
   setup_deployment_endpoints(app, recommendations_store)
   
3. Your endpoints will be available at:
   POST   /api/v1/recommendations/{id}/deploy
   GET    /api/v1/products
   GET    /api/v1/products/{id}/status
   DELETE /api/v1/products/{id}
"""

from fastapi import FastAPI, HTTPException, APIRouter
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime

try:
    from flink_job_deployer import FlinkJobDeployer, create_deployer
    FLINK_AVAILABLE = True
except ImportError:
    FLINK_AVAILABLE = False
    FlinkJobDeployer = None
    create_deployer = None
    print("⚠️  Flink job deployer not available - deployment features disabled")

logger = logging.getLogger(__name__)

# Global state (will be initialized by setup function)
_deployer: Optional[FlinkJobDeployer] = None
_recommendations_store: Optional[Dict[str, Dict[str, Any]]] = None


# === REQUEST/RESPONSE MODELS ===

class DeployResponse(BaseModel):
    """Response from deployment"""
    success: bool
    product_id: str
    flink_job_id: Optional[str] = None
    status: str
    message: str
    created_topics: List[str] = []


class ProductStatusResponse(BaseModel):
    """Product health status"""
    product_id: str
    product_name: str = "Unknown"  # Default value to handle None
    flink_job_id: Optional[str]
    status: str
    is_running: bool
    deployed_at: Optional[str] = None
    start_time: Optional[int] = None
    duration: Optional[int] = None


class StopProductRequest(BaseModel):
    """Request to stop a product"""
    reason: Optional[str] = None


# === SETUP FUNCTION ===

def setup_deployment_endpoints(
    app: FastAPI,
    recommendations_store: Dict[str, Dict[str, Any]]
):
    """
    Setup deployment endpoints with access to recommendations_store
    
    Args:
        app: FastAPI application
        recommendations_store: Your existing recommendations dict
    """
    global _deployer, _recommendations_store
    
    # Initialize Flink deployer
    try:
        _deployer = create_deployer(
            flink_url="http://localhost:8085",
            kafka_bootstrap="kafka:9092"
        )
        logger.info("✅ Flink deployer initialized")
    except Exception as e:
        logger.warning(f"⚠️ Could not initialize Flink deployer: {e}")
        _deployer = None
    
    # Store reference to recommendations
    _recommendations_store = recommendations_store
    
    # Create router
    router = APIRouter(prefix="/api/v1", tags=["deployment"])
    
    # === ENDPOINTS ===
    
    @router.post("/recommendations/{recommendation_id}/deploy", response_model=DeployResponse)
    async def deploy_recommendation(recommendation_id: str):
        """
        Deploy an AI recommendation as a live Flink job
        
        Workflow:
        1. Fetch recommendation from recommendations_store
        2. Create Kafka topic for the product
        3. Submit Flink SQL job
        4. Update recommendation with job_id and status=ACTIVE
        """
        if not _deployer:
            raise HTTPException(
                status_code=503,
                detail="Flink deployer not available. Is Flink running?"
            )
        
        if not _recommendations_store:
            raise HTTPException(
                status_code=503,
                detail="Recommendations store not initialized"
            )
        
        # Get recommendation
        if recommendation_id not in _recommendations_store:
            raise HTTPException(
                status_code=404,
                detail=f"Recommendation {recommendation_id} not found"
            )
        
        rec = _recommendations_store[recommendation_id]
        
        # Extract product name early for use throughout function
        product_name = rec.get("product_name", "Unnamed Product")
        
        # Check if already deployed
        if rec.get("status") == "ACTIVE":
            raise HTTPException(
                status_code=400,
                detail=f"Recommendation already deployed (job: {rec.get('flink_job_id')})"
            )
        
        logger.info(f"Deploying recommendation: {product_name}")
        
        try:
            # Update status to DEPLOYING
            rec["status"] = "DEPLOYING"
            rec["deployment_started_at"] = datetime.utcnow().isoformat()
            
            # Prepare recommendation for deployer
            flink_sql = rec.get("flink_sql")
            
            if not flink_sql:
                raise HTTPException(
                    status_code=400,
                    detail="Recommendation missing required 'flink_sql' field"
                )
            
            deployment_rec = {
                "product_id": recommendation_id,
                "product_name": product_name,
                "flink_sql": flink_sql,
                "output_topic": rec.get("output_topic", f"product.{recommendation_id}")
            }
            
            # Deploy via Flink
            result = _deployer.deploy_recommendation(deployment_rec)
            
            if result.success:
                # Update recommendation with deployment info
                rec["status"] = "ACTIVE"
                rec["flink_job_id"] = result.flink_job_id
                rec["deployed_at"] = datetime.utcnow().isoformat()
                rec["output_topic"] = deployment_rec["output_topic"]
                rec["created_topics"] = result.created_topics
                
                logger.info(f"✅ Deployed {product_name} with job {result.flink_job_id}")
                
                return DeployResponse(
                    success=True,
                    product_id=recommendation_id,
                    flink_job_id=result.flink_job_id,
                    status="ACTIVE",
                    message=f"Product '{product_name}' deployed successfully",
                    created_topics=result.created_topics
                )
            else:
                # Deployment failed
                rec["status"] = "FAILED"
                rec["error"] = result.error_message
                rec["failed_at"] = datetime.utcnow().isoformat()
                
                raise HTTPException(
                    status_code=500,
                    detail=f"Deployment failed: {result.error_message}"
                )
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Deployment error: {e}")
            rec["status"] = "FAILED"
            rec["error"] = str(e)
            raise HTTPException(status_code=500, detail=str(e))
    
    
    @router.get("/products", response_model=List[Dict[str, Any]])
    async def list_deployed_products():
        """
        List all deployed data products
        
        Returns recommendations that have been deployed (status=ACTIVE)
        enriched with current Flink job status
        """
        if not _deployer:
            raise HTTPException(
                status_code=503,
                detail="Flink deployer not available"
            )
        
        if not _recommendations_store:
            raise HTTPException(
                status_code=503,
                detail="Recommendations store not initialized"
            )
        
        try:
            # Get all active products from recommendations_store
            products = [
                rec for rec in _recommendations_store.values()
                if rec.get("status") in ["ACTIVE", "DEPLOYING", "FAILED"]
            ]
            
            # Enrich with current Flink status
            active_jobs = _deployer.list_active_products()
            job_status_map = {job["job_id"]: job for job in active_jobs}
            
            enriched = []
            for product in products:
                job_id = product.get("flink_job_id")
                
                enriched_product = {
                    "product_id": product.get("recommendation_id", "unknown"),
                    "product_name": product.get("product_name", "Unknown"),
                    "product_type": product.get("product_type", "UNKNOWN"),
                    "status": product.get("status", "UNKNOWN"),
                    "flink_job_id": job_id,
                    "deployed_at": product.get("deployed_at"),
                    "output_topic": product.get("output_topic"),
                    "source_topics": product.get("source_topics", [])
                }
                
                # Add runtime status from Flink
                if job_id and job_id in job_status_map:
                    flink_job = job_status_map[job_id]
                    enriched_product["flink_status"] = flink_job["status"]
                    enriched_product["is_running"] = flink_job["is_running"]
                else:
                    enriched_product["flink_status"] = "UNKNOWN"
                    enriched_product["is_running"] = False
                
                enriched.append(enriched_product)
            
            return enriched
            
        except Exception as e:
            logger.error(f"Error listing products: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    
    @router.get("/products/{product_id}/status", response_model=ProductStatusResponse)
    async def get_product_status(product_id: str):
        """
        Get detailed status for a specific deployed product
        
        Includes:
        - Database status from recommendations_store
        - Real-time Flink job status
        - Performance metrics
        """
        if not _deployer:
            raise HTTPException(
                status_code=503,
                detail="Flink deployer not available"
            )
        
        if not _recommendations_store:
            raise HTTPException(
                status_code=503,
                detail="Recommendations store not initialized"
            )
        
        # Get product
        if product_id not in _recommendations_store:
            raise HTTPException(
                status_code=404,
                detail=f"Product {product_id} not found"
            )
        
        product = _recommendations_store[product_id]
        flink_job_id = product.get("flink_job_id")
        
        if not flink_job_id:
            return ProductStatusResponse(
                product_id=product_id,
                product_name=product.get("product_name", "Unknown"),
                flink_job_id=None,
                status="NOT_DEPLOYED",
                is_running=False,
                deployed_at=None
            )
        
        try:
            # Get real-time Flink status
            flink_status = _deployer.get_product_status(flink_job_id)
            
            return ProductStatusResponse(
                product_id=product_id,
                product_name=product.get("product_name", "Unknown"),
                flink_job_id=flink_job_id,
                status=flink_status["status"],
                is_running=flink_status.get("is_running", False),
                deployed_at=product.get("deployed_at"),
                start_time=flink_status.get("start_time"),
                duration=flink_status.get("duration")
            )
            
        except Exception as e:
            logger.error(f"Error getting product status: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    
    @router.delete("/products/{product_id}")
    async def stop_product(product_id: str, request: Optional[StopProductRequest] = None):
        """
        Stop a running data product
        
        Cancels the Flink job and updates product status to STOPPED
        """
        if not _deployer:
            raise HTTPException(
                status_code=503,
                detail="Flink deployer not available"
            )
        
        if not _recommendations_store:
            raise HTTPException(
                status_code=503,
                detail="Recommendations store not initialized"
            )
        
        # Get product
        if product_id not in _recommendations_store:
            raise HTTPException(
                status_code=404,
                detail=f"Product {product_id} not found"
            )
        
        product = _recommendations_store[product_id]
        flink_job_id = product.get("flink_job_id")
        
        if not flink_job_id:
            raise HTTPException(
                status_code=400,
                detail="Product not deployed"
            )
        
        try:
            # Cancel Flink job
            success = _deployer.stop_product(flink_job_id)
            
            if success:
                # Update product status
                product["status"] = "STOPPED"
                product["stopped_at"] = datetime.utcnow().isoformat()
                if request and request.reason:
                    product["stop_reason"] = request.reason
                
                product_name = product.get("product_name", "Unknown")
                logger.info(f"✅ Stopped product {product_name}")
                
                return {
                    "success": True,
                    "product_id": product_id,
                    "message": f"Product '{product_name}' stopped successfully"
                }
            else:
                raise HTTPException(
                    status_code=500,
                    detail="Failed to cancel Flink job"
                )
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error stopping product: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    
    @router.get("/flink/health")
    async def check_flink_health():
        """Check if Flink cluster is healthy"""
        if not _deployer:
            return {
                "healthy": False,
                "message": "Flink deployer not initialized"
            }
        
        try:
            healthy = _deployer.flink.health_check()
            
            if healthy:
                overview = _deployer.flink.get_cluster_overview()
                return {
                    "healthy": True,
                    "taskmanagers": overview.get("taskmanagers"),
                    "slots_total": overview.get("slots-total"),
                    "slots_available": overview.get("slots-available"),
                    "jobs_running": overview.get("jobs-running")
                }
            else:
                return {
                    "healthy": False,
                    "message": "Cannot connect to Flink"
                }
                
        except Exception as e:
            return {
                "healthy": False,
                "error": str(e)
            }
    
    # Add router to app
    app.include_router(router)
    logger.info("✅ Deployment endpoints registered")


# === USAGE EXAMPLE ===
"""
In your catalog_api.py:

# At the top, add import:
from deployment_integration import setup_deployment_endpoints

# After creating recommendations_store:
recommendations_store: Dict[str, Dict[str, Any]] = {}

# After creating FastAPI app:
app = FastAPI(lifespan=lifespan)

# Setup deployment endpoints:
setup_deployment_endpoints(app, recommendations_store)

# Now you have these new endpoints:
# POST   /api/v1/recommendations/{id}/deploy
# GET    /api/v1/products
# GET    /api/v1/products/{id}/status  
# DELETE /api/v1/products/{id}
# GET    /api/v1/flink/health
"""