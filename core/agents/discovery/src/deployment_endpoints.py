"""
New API Endpoints for Product Deployment

Add these endpoints to your Discovery Agent's catalog_api.py

These endpoints bridge AI recommendations → Flink deployment
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import logging

from flink_job_deployer import FlinkJobDeployer, create_deployer, ProductStatus, DeploymentResult

logger = logging.getLogger(__name__)

# Create router (add to your FastAPI app)
deployment_router = APIRouter(prefix="/api/v1", tags=["deployment"])

# Global deployer instance (or inject via dependency)
_deployer: Optional[FlinkJobDeployer] = None


def get_deployer() -> FlinkJobDeployer:
    """Get or create FlinkJobDeployer instance"""
    global _deployer
    if _deployer is None:
        _deployer = create_deployer(
            flink_url="http://localhost:8085",
            kafka_bootstrap="kafka:9092"
        )
    return _deployer


# Request/Response Models

class DeployRequest(BaseModel):
    """Request to deploy a recommendation"""
    recommendation_id: str
    auto_start: bool = True  # Start immediately after deployment


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
    flink_job_id: Optional[str]
    status: str
    is_running: bool
    start_time: Optional[int]
    duration: Optional[int]
    metrics: Dict[str, Any] = {}


class StopProductRequest(BaseModel):
    """Request to stop a product"""
    product_id: str
    reason: Optional[str] = None


# === DEPLOYMENT ENDPOINTS ===

@deployment_router.post("/recommendations/{recommendation_id}/deploy", response_model=DeployResponse)
async def deploy_recommendation(
    recommendation_id: str,
    background_tasks: BackgroundTasks,
    request: Optional[DeployRequest] = None
):
    """
    Deploy an AI recommendation as a live Flink job
    
    This endpoint:
    1. Fetches the recommendation from database
    2. Creates the output Kafka topic
    3. Submits Flink SQL job
    4. Updates product status to ACTIVE
    
    Args:
        recommendation_id: Recommendation to deploy
        request: Optional deployment configuration
        
    Returns:
        Deployment result with job ID
    """
    logger.info(f"Deploying recommendation: {recommendation_id}")
    
    try:
        # Fetch recommendation from database
        # In real implementation, you'd query your database
        recommendation = await _fetch_recommendation(recommendation_id)
        
        if not recommendation:
            raise HTTPException(
                status_code=404,
                detail=f"Recommendation {recommendation_id} not found"
            )
        
        # Check if already deployed
        if recommendation.get("status") == "ACTIVE":
            raise HTTPException(
                status_code=400,
                detail="Recommendation already deployed"
            )
        
        # Update status to DEPLOYING
        await _update_recommendation_status(recommendation_id, ProductStatus.DEPLOYING)
        
        # Deploy via FlinkJobDeployer
        deployer = get_deployer()
        result = deployer.deploy_recommendation(recommendation)
        
        if result.success:
            # Update database with job ID and ACTIVE status
            if result.flink_job_id:
                await _update_recommendation_deployment(
                    recommendation_id,
                    flink_job_id=result.flink_job_id,
                    status=ProductStatus.ACTIVE
                )
            else:
                # Job submitted but no ID returned (rare)
                await _update_recommendation_status(
                    recommendation_id,
                    ProductStatus.ACTIVE
                )
            
            return DeployResponse(
                success=True,
                product_id=recommendation_id,
                flink_job_id=result.flink_job_id,
                status="ACTIVE",
                message="Product deployed successfully",
                created_topics=result.created_topics
            )
        else:
            # Update status to FAILED
            await _update_recommendation_status(
                recommendation_id,
                ProductStatus.FAILED,
                error=result.error_message
            )
            
            raise HTTPException(
                status_code=500,
                detail=f"Deployment failed: {result.error_message}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Deployment error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@deployment_router.get("/products", response_model=List[Dict[str, Any]])
async def list_products():
    """
    List all deployed data products
    
    Returns products with their current status from both:
    - Database (product metadata)
    - Flink (runtime status)
    """
    try:
        # Fetch products from database
        products = await _fetch_all_products()
        
        # Enrich with Flink status
        deployer = get_deployer()
        active_jobs = deployer.list_active_products()
        
        # Create job_id → status map
        job_status = {job["job_id"]: job for job in active_jobs}
        
        # Enrich products
        enriched = []
        for product in products:
            job_id = product.get("flink_job_id")
            if job_id and job_id in job_status:
                product["runtime_status"] = job_status[job_id]["status"]
                product["is_running"] = job_status[job_id]["is_running"]
            else:
                product["runtime_status"] = "UNKNOWN"
                product["is_running"] = False
            
            enriched.append(product)
        
        return enriched
        
    except Exception as e:
        logger.error(f"Error listing products: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@deployment_router.get("/products/{product_id}/status", response_model=ProductStatusResponse)
async def get_product_status(product_id: str):
    """
    Get detailed status for a specific product
    
    Includes:
    - Database status
    - Flink job status
    - Performance metrics
    """
    try:
        # Fetch product from database
        product = await _fetch_product(product_id)
        
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        flink_job_id = product.get("flink_job_id")
        
        if not flink_job_id:
            return ProductStatusResponse(
                product_id=product_id,
                flink_job_id=None,
                status="NOT_DEPLOYED",
                is_running=False,
                start_time=None,
                duration=None
            )
        
        # Get Flink status
        deployer = get_deployer()
        status = deployer.get_product_status(flink_job_id)
        
        return ProductStatusResponse(
            product_id=product_id,
            flink_job_id=flink_job_id,
            status=status["status"],
            is_running=status.get("is_running", False),
            start_time=status.get("start_time"),
            duration=status.get("duration"),
            metrics=status.get("metrics", {})
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting product status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@deployment_router.delete("/products/{product_id}")
async def stop_product(product_id: str, request: Optional[StopProductRequest] = None):
    """
    Stop a running data product
    
    This cancels the Flink job and updates product status to STOPPED
    """
    try:
        # Fetch product
        product = await _fetch_product(product_id)
        
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        flink_job_id = product.get("flink_job_id")
        
        if not flink_job_id:
            raise HTTPException(status_code=400, detail="Product not deployed")
        
        # Cancel Flink job
        deployer = get_deployer()
        success = deployer.stop_product(flink_job_id)
        
        if success:
            # Update database status
            await _update_recommendation_status(
                product_id,
                ProductStatus.STOPPED,
                reason=request.reason if request else None
            )
            
            return {
                "success": True,
                "message": f"Product {product_id} stopped successfully"
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


# === DATABASE HELPER FUNCTIONS ===
# These need to be implemented based on your actual database setup

async def _fetch_recommendation(recommendation_id: str) -> Optional[Dict[str, Any]]:
    """Fetch recommendation from database"""
    # TODO: Implement with your database
    # Example:
    # return db.query(Recommendation).filter(id=recommendation_id).first()
    raise NotImplementedError("Connect to your database")


async def _fetch_product(product_id: str) -> Optional[Dict[str, Any]]:
    """Fetch product from database"""
    # TODO: Implement with your database
    raise NotImplementedError("Connect to your database")


async def _fetch_all_products() -> List[Dict[str, Any]]:
    """Fetch all products from database"""
    # TODO: Implement with your database
    raise NotImplementedError("Connect to your database")


async def _update_recommendation_status(
    recommendation_id: str,
    status: ProductStatus,
    error: Optional[str] = None,
    reason: Optional[str] = None
):
    """Update recommendation status in database"""
    # TODO: Implement with your database
    logger.info(f"Updating {recommendation_id} to {status}")


async def _update_recommendation_deployment(
    recommendation_id: str,
    flink_job_id: Optional[str],
    status: ProductStatus
):
    """Update recommendation with deployment details"""
    # TODO: Implement with your database
    logger.info(f"Product {recommendation_id} deployed with job {flink_job_id}")


# === HEALTH CHECK ===

@deployment_router.get("/flink/health")
async def check_flink_health():
    """Check if Flink cluster is healthy"""
    try:
        deployer = get_deployer()
        healthy = deployer.flink.health_check()
        
        if healthy:
            overview = deployer.flink.get_cluster_overview()
            return {
                "healthy": True,
                "taskmanagers": overview.get("taskmanagers"),
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


# === HOW TO ADD TO YOUR APP ===
"""
In your catalog_api.py or main FastAPI app:

from deployment_endpoints import deployment_router

app = FastAPI()
app.include_router(deployment_router)

Then you'll have these endpoints:
- POST   /api/v1/recommendations/{id}/deploy
- GET    /api/v1/products
- GET    /api/v1/products/{id}/status
- DELETE /api/v1/products/{id}
- GET    /api/v1/flink/health
"""