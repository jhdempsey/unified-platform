"""
Enhanced Data Catalog API with AI Product Recommendations
Shows managed products + discovered topics with AI-generated recommendations
"""

import os
import sys
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Query, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from shared.config import config
from deployment_integration import setup_deployment_endpoints

# ============================================================================
# SETUP IMPORTS - Make product_recommender discoverable
# ============================================================================
# Add parent directory to path so we can import from sibling packages
_current_file = Path(__file__).resolve()
_agents_dir = _current_file.parent.parent
_recommender_dir = _agents_dir / "product-recommender-agent"

if str(_agents_dir) not in sys.path:
    sys.path.insert(0, str(_agents_dir))
if str(_recommender_dir) not in sys.path:
    sys.path.insert(0, str(_recommender_dir))

# Now import - VS Code will see these in sys.path
from topic_discovery import TopicDiscoveryAgent
from schema_analyzer import SchemaSimilarityAnalyzer
from product_recommender import ProductRecommenderAgent, ProductRecommendation


# ============================================================================
# Pydantic Models - Original Discovery Models
# ============================================================================

class DataSource(BaseModel):
    """Unified data source (managed product or discovered topic)"""
    name: str
    type: str  # "MANAGED_PRODUCT" or "DISCOVERED_TOPIC"
    status: str  # "GOVERNED", "UNMANAGED", "CANDIDATE"
    topic_name: Optional[str] = None
    product_id: Optional[str] = None
    schema_definition: Optional[Dict[str, Any]] = None  # Renamed from 'schema' to avoid warning
    quality_score: Optional[float] = None
    partitions: Optional[int] = None
    owner: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    discovered_at: Optional[datetime] = None
    issues: List[str] = Field(default_factory=list)


class SearchRequest(BaseModel):
    """Search request"""
    query: str
    filters: Optional[Dict[str, Any]] = None
    include_unmanaged: bool = True


class SearchResults(BaseModel):
    """Search results with recommendations"""
    query: str
    results: List[DataSource]
    recommendations: List[Dict[str, Any]] = Field(default_factory=list)
    total_found: int


class PromoteRequest(BaseModel):
    """Request to promote discovered topic to managed product"""
    topic_name: str
    product_name: str
    owner: str
    description: str


# ============================================================================
# Pydantic Models - Recommendation Models
# ============================================================================

class RecommendationResponse(BaseModel):
    """Response model for a recommendation"""
    recommendation_id: str
    product_name: str
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str
    source_topics: List[str]
    proposed_output_topic: str
    proposed_schema: Dict[str, Any]
    flink_sql: str
    business_value: str
    estimated_consumers: int = 0
    priority: str  # HIGH, MEDIUM, LOW
    created_at: str
    status: str  # PENDING_REVIEW, APPROVED, REJECTED, DEPLOYED


class RefineRequest(BaseModel):
    """Request to refine a recommendation"""
    user_feedback: str = Field(
        description="User's feedback or requested changes"
    )


class ApprovalRequest(BaseModel):
    """Request to approve and deploy a recommendation"""
    approved_by: str
    modifications: Optional[Dict[str, Any]] = None
    deploy_immediately: bool = True


# ============================================================================
# Global State
# ============================================================================

# Discovery state - with type hints for VS Code
discovery_agent: Optional[TopicDiscoveryAgent] = None
analyzer: Optional[SchemaSimilarityAnalyzer] = None
recommender_agent: Optional[ProductRecommenderAgent] = None
cached_discovered_topics: List[Dict[str, Any]] = []
cached_analysis: Dict[str, Any] = {}
last_discovery_time: Optional[datetime] = None

# Recommendations store (in production, use PostgreSQL)
recommendations_store: Dict[str, Dict[str, Any]] = {}


# ============================================================================
# Lifespan Management (replaces deprecated @app.on_event)
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup/shutdown
    Replaces deprecated @app.on_event("startup")
    """
    # Startup
    global discovery_agent, analyzer, recommender_agent
    global cached_discovered_topics, cached_analysis
    
    print("🚀 Starting Enhanced Data Catalog API...")
    
    try:
        # Initialize agents
        discovery_agent = TopicDiscoveryAgent(sample_size=50)
        analyzer = SchemaSimilarityAnalyzer()
        recommender_agent = ProductRecommenderAgent()
        print("✅ Agents initialized")
        
        # Try initial discovery, but don't fail startup if it errors
        try:
            await refresh_discovery()
            print("✅ Initial discovery complete")
        except Exception as e:
            print(f"⚠️  Initial discovery failed (will retry later): {e}")
            # Initialize empty cache so the service can still start
            cached_discovered_topics = []
            cached_analysis = {
                "recommendations": [],
                "unmanaged": [],
                "analyzed_at": None
            }
        
        print("✅ Enhanced Catalog API ready")
        
    except Exception as e:
        print(f"❌ Initialization failed: {e}")
        raise  # Re-raise to prevent service from starting in a bad state
    
    # Yield control to the application
    yield
    
    # Shutdown (if needed)
    print("👋 Shutting down Enhanced Catalog API...")


# ============================================================================
# Create FastAPI App
# ============================================================================

app = FastAPI(
    title="Enhanced Data Catalog API",
    description="Intelligent catalog with AI-powered product recommendations",
    version="2.0.0",
    lifespan=lifespan  # Use lifespan instead of @app.on_event
)

# Setup deployment endpoints
setup_deployment_endpoints(app, recommendations_store)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# Health & Root Endpoints
# ============================================================================

@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "discovery-agent",
        "timestamp": datetime.utcnow().isoformat(),
        "agents": {
            "discovery": discovery_agent is not None,
            "analyzer": analyzer is not None,
            "recommender": recommender_agent is not None
        }
    }


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint"""
    return {
        "service": "Enhanced Data Catalog with AI Recommendations",
        "version": "2.0.0",
        "capabilities": [
            "Discover all Kafka topics",
            "Compare schema similarity",
            "Detect redundancy",
            "AI-powered product recommendations",
            "Recommend consolidation",
            "Promote to managed products",
            "Interactive recommendation refinement"
        ]
    }


# ============================================================================
# Discovery Functions
# ============================================================================

async def refresh_discovery():
    """Refresh discovered topics with detailed step-by-step logging"""
    global cached_discovered_topics, cached_analysis, last_discovery_time
    
    print("=" * 70)
    print("🔄 STARTING DISCOVERY REFRESH")
    print("=" * 70)
    
    recommendations = []
    unmanaged = []
    managed_topics = []
    
    try:
        # STEP 1: Discover Topics
        print("\n📍 STEP 1: Discovering Kafka topics...")
        try:
            cached_discovered_topics = discovery_agent.discover_and_analyze_all()
            print(f"   ✅ SUCCESS: Discovered {len(cached_discovered_topics)} topics")
        except Exception as e:
            print(f"   ❌ STEP 1 FAILED: {e}")
            import traceback
            traceback.print_exc()
            raise
        
        # STEP 2: Analyze for Recommendations (Schema Similarity)
        print("\n📍 STEP 2: Analyzing schema similarity...")
        try:
            valid_topics = [t for t in cached_discovered_topics if t and isinstance(t, dict)]
            print(f"   ✅ Validated {len(valid_topics)}/{len(cached_discovered_topics)} topics")
            
            if valid_topics:
                recommendations = analyzer.compare_topics(valid_topics)
                print(f"   ✅ SUCCESS: Found {len(recommendations)} consolidation opportunities")
            else:
                recommendations = []
        except Exception as e:
            print(f"   ❌ STEP 2 FAILED: {e}")
            import traceback
            traceback.print_exc()
            recommendations = []
        
        # STEP 3: Get Managed Topics
        print("\n📍 STEP 3: Fetching managed topics...")
        try:
            managed_topics = await get_managed_topics()
            print(f"   ✅ SUCCESS: Found {len(managed_topics)} managed topics")
        except Exception as e:
            print(f"   ❌ STEP 3 FAILED: {e}")
            import traceback
            traceback.print_exc()
            managed_topics = []
        
        # STEP 4: Detect Unmanaged
        print("\n📍 STEP 4: Detecting unmanaged topics...")
        try:
            if cached_discovered_topics and managed_topics is not None:
                unmanaged = analyzer.detect_unmanaged_topics(
                    cached_discovered_topics,
                    managed_topics
                )
                print(f"   ✅ SUCCESS: Found {len(unmanaged)} unmanaged topics")
            else:
                unmanaged = []
        except Exception as e:
            print(f"   ❌ STEP 4 FAILED: {e}")
            import traceback
            traceback.print_exc()
            unmanaged = []
        
        # STEP 5: Store Results
        print("\n📍 STEP 5: Storing results...")
        cached_analysis = {
            "recommendations": recommendations,
            "unmanaged": unmanaged,
            "analyzed_at": datetime.utcnow().isoformat()
        }
        last_discovery_time = datetime.utcnow()
        print("   ✅ SUCCESS: Results stored")
        
        # Summary
        print("\n" + "=" * 70)
        print("✅ DISCOVERY COMPLETE")
        print("=" * 70)
        print(f"📊 Summary:")
        print(f"   Topics discovered:          {len(cached_discovered_topics)}")
        print(f"   Consolidation opportunities: {len(recommendations)}")
        print(f"   Managed topics:             {len(managed_topics)}")
        print(f"   Unmanaged topics:           {len(unmanaged)}")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n❌ DISCOVERY FAILED: {e}")
        import traceback
        traceback.print_exc()
        
        # Initialize empty cache
        cached_discovered_topics = []
        cached_analysis = {
            "recommendations": [],
            "unmanaged": [],
            "analyzed_at": None
        }


async def get_managed_topics() -> List[str]:
    """Get list of managed topics from Product Service"""
    try:
        import requests
        
        url = f"{config.PRODUCT_SERVICE_URL}/products"
        response = requests.get(url, timeout=5)
        
        if response.status_code != 200:
            return []
        
        data = response.json()
        if not isinstance(data, dict):
            return []
        
        products = data.get("products")
        if not isinstance(products, list):
            return []
        
        topics = []
        for product in products:
            if product and isinstance(product, dict):
                topic = product.get("kafka_topic")
                if topic and isinstance(topic, str):
                    topics.append(topic)
        
        return topics
        
    except Exception as e:
        print(f"⚠️  Error fetching managed topics: {e}")
        return []


# ============================================================================
# Discovery Endpoints
# ============================================================================

@app.get("/discover", tags=["Discovery"])
async def trigger_discovery():
    """Manually trigger topic discovery"""
    await refresh_discovery()
    
    return {
        "status": "complete",
        "topics_discovered": len(cached_discovered_topics),
        "recommendations": len(cached_analysis.get("recommendations", [])),
        "unmanaged_topics": len(cached_analysis.get("unmanaged", [])),
        "discovered_at": last_discovery_time.isoformat() if last_discovery_time else None
    }


@app.post("/search", response_model=SearchResults, tags=["Search"])
async def search_data_sources(request: SearchRequest):
    """
    Search across ALL data sources (managed + discovered)
    Returns unified results with AI recommendations
    """
    query = request.query.lower()
    results = []
    
    # Search managed products
    try:
        import requests
        response = requests.get(
            f"{config.PRODUCT_SERVICE_URL}/products?search={query}",
            timeout=5
        )
        if response.status_code == 200:
            products = response.json()["products"]
            for product in products:
                results.append(DataSource(
                    name=product["product_name"],
                    type="MANAGED_PRODUCT",
                    status="GOVERNED",
                    product_id=product["product_id"],
                    topic_name=product.get("kafka_topic"),
                    schema_definition=product.get("schema_definition"),
                    quality_score=product.get("quality_score"),
                    owner=product.get("owner"),
                    tags=product.get("tags", [])
                ))
    except Exception as e:
        print(f"⚠️  Could not fetch managed products: {e}")
    
    # Search discovered topics
    if request.include_unmanaged:
        for topic in cached_discovered_topics:
            topic_name = topic["topic_name"]
            if query in topic_name.lower():
                is_managed = any(r.topic_name == topic_name for r in results)
                
                if not is_managed:
                    quality_score = analyzer._assess_quality(topic)
                    
                    results.append(DataSource(
                        name=topic_name,
                        type="DISCOVERED_TOPIC",
                        status="UNMANAGED" if quality_score < 70 else "CANDIDATE",
                        topic_name=topic_name,
                        schema_definition=topic.get("inferred_schema"),
                        quality_score=quality_score,
                        partitions=topic.get("partitions"),
                        discovered_at=topic.get("discovered_at"),
                        issues=analyzer._identify_issues(topic),
                        tags=[]
                    ))
    
    # Find relevant recommendations
    recommendations = []
    for rec in cached_analysis.get("recommendations", []):
        if any(query in topic.lower() for topic in rec["topics"]):
            recommendations.append(rec)
    
    return SearchResults(
        query=request.query,
        results=results,
        recommendations=recommendations,
        total_found=len(results)
    )


@app.get("/recommendations_old", tags=["Intelligence"])
async def get_recommendations():
    """Get all consolidation and governance recommendations (old schema-based)"""
    return {
        "consolidation_opportunities": cached_analysis.get("recommendations", []),
        "unmanaged_topics": cached_analysis.get("unmanaged", []),
        "analyzed_at": cached_analysis.get("analyzed_at")
    }


@app.get("/topics/{topic_name}/analysis", tags=["Analysis"])
async def analyze_topic(topic_name: str):
    """Get detailed analysis for a specific topic"""
    topic = next(
        (t for t in cached_discovered_topics if t["topic_name"] == topic_name),
        None
    )
    
    if not topic:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Topic {topic_name} not found"
        )
    
    quality_score = analyzer._assess_quality(topic)
    issues = analyzer._identify_issues(topic)
    
    related = []
    for other_topic in cached_discovered_topics:
        if other_topic["topic_name"] != topic_name:
            similarity = analyzer._calculate_similarity(topic, other_topic)
            if similarity["overlap_percentage"] > 30:
                related.append({
                    "topic_name": other_topic["topic_name"],
                    "similarity": similarity
                })
    
    return {
        "topic_name": topic_name,
        "quality_score": quality_score,
        "issues": issues,
        "schema": topic.get("inferred_schema"),
        "patterns": topic.get("patterns"),
        "field_coverage": topic.get("field_coverage"),
        "related_topics": related,
        "recommended_action": analyzer._suggest_action(topic, quality_score)
    }


@app.post("/promote", tags=["Management"])
async def promote_to_managed(request: PromoteRequest):
    """
    Promote a discovered topic to a managed data product
    """
    topic = next(
        (t for t in cached_discovered_topics if t["topic_name"] == request.topic_name),
        None
    )
    
    if not topic:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Topic {request.topic_name} not found"
        )
    
    try:
        import requests
        
        product_data = {
            "product_name": request.product_name,
            "product_type": "STREAM",
            "owner": request.owner,
            "description": request.description,
            "kafka_topic": request.topic_name,
            "schema_definition": topic.get("inferred_schema"),
            "schema_version": "1.0.0",
            "tags": ["promoted", "discovered"],
            "created_by": "DISCOVERY_AGENT"
        }
        
        response = requests.post(
            f"{config.PRODUCT_SERVICE_URL}/products",
            json=product_data,
            timeout=10
        )
        
        if response.status_code == 201:
            product = response.json()
            await refresh_discovery()
            
            return {
                "success": True,
                "product_id": product["product_id"],
                "message": f"Topic {request.topic_name} promoted to managed product"
            }
        else:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Product Service error: {response.text}"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Promotion failed: {str(e)}"
        )


@app.get("/stats", tags=["Statistics"])
async def get_stats():
    """Get catalog statistics"""
    managed_count = 0
    try:
        import requests
        response = requests.get(f"{config.PRODUCT_SERVICE_URL}/stats", timeout=5)
        if response.status_code == 200:
            managed_count = response.json()["total_products"]
    except:
        pass
    
    discovered_count = len(cached_discovered_topics)
    unmanaged_count = len(cached_analysis.get("unmanaged", []))
    recommendations_count = len(cached_analysis.get("recommendations", []))
    
    return {
        "total_data_sources": managed_count + discovered_count,
        "managed_products": managed_count,
        "discovered_topics": discovered_count,
        "unmanaged_topics": unmanaged_count,
        "consolidation_opportunities": recommendations_count,
        "ai_recommendations": len(recommendations_store),
        "governance_coverage": (managed_count / discovered_count * 100) if discovered_count > 0 else 0,
        "last_discovery": last_discovery_time.isoformat() if last_discovery_time else None
    }


# ============================================================================
# AI Recommendation Endpoints (NEW!)
# ============================================================================

@app.post("/recommendations/generate", tags=["AI Recommendations"])
async def generate_recommendations(max_recommendations: int = 10):
    """
    Generate AI-powered product recommendations based on discovered topics
    
    This uses Claude AI to analyze discovered topics and recommend
    high-value data products that should be created.
    """
    global recommendations_store
    
    print(f"🤖 Generating up to {max_recommendations} AI recommendations...")
    
    try:
        if not cached_discovered_topics:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No topics discovered yet. Run /discover first."
            )
        
        # Use ProductRecommenderAgent
        recommendations = recommender_agent.analyze_and_recommend(
            cached_discovered_topics,
            max_recommendations=max_recommendations
        )
        
        # Store recommendations
        for rec in recommendations:
            recommendations_store[rec.recommendation_id] = rec.to_dict()
        
        print(f"✅ Generated {len(recommendations)} AI recommendations")
        
        return {
            "status": "success",
            "total_recommendations": len(recommendations),
            "recommendations": [rec.to_dict() for rec in recommendations],
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        print(f"❌ Failed to generate recommendations: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate recommendations: {str(e)}"
        )


@app.get(
    "/recommendations",
    response_model=List[RecommendationResponse],
    tags=["AI Recommendations"]
)
async def list_recommendations(
    status_filter: Optional[str] = None,
    priority_filter: Optional[str] = None
):
    """List all AI-generated product recommendations"""
    results = list(recommendations_store.values())
    
    if status_filter:
        results = [r for r in results if r["status"] == status_filter.upper()]
    
    if priority_filter:
        results = [r for r in results if r["priority"] == priority_filter.upper()]
    
    results.sort(key=lambda x: x["confidence"], reverse=True)
    
    return results


@app.get(
    "/recommendations/{recommendation_id}",
    response_model=RecommendationResponse,
    tags=["AI Recommendations"]
)
async def get_recommendation(recommendation_id: str):
    """Get details of a specific recommendation"""
    
    if recommendation_id not in recommendations_store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Recommendation {recommendation_id} not found"
        )
    
    return recommendations_store[recommendation_id]


@app.put(
    "/recommendations/{recommendation_id}",
    response_model=RecommendationResponse,
    tags=["AI Recommendations"]
)
async def update_recommendation(
    recommendation_id: str,
    updates: Dict[str, Any]
):
    """Update a recommendation manually"""
    
    if recommendation_id not in recommendations_store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Recommendation {recommendation_id} not found"
        )
    
    rec = recommendations_store[recommendation_id]
    
    allowed_fields = [
        "product_name",
        "proposed_schema",
        "source_topics",
        "flink_sql",
        "priority",
        "proposed_output_topic"
    ]
    
    for field in allowed_fields:
        if field in updates:
            rec[field] = updates[field]
    
    rec["updated_at"] = datetime.utcnow().isoformat()
    recommendations_store[recommendation_id] = rec
    
    print(f"✅ Updated recommendation: {recommendation_id}")
    
    return rec


@app.post(
    "/recommendations/{recommendation_id}/refine",
    response_model=RecommendationResponse,
    tags=["AI Recommendations"]
)
async def refine_recommendation(
    recommendation_id: str,
    request: RefineRequest
):
    """Use AI to refine a recommendation based on user feedback"""
    
    if recommendation_id not in recommendations_store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Recommendation {recommendation_id} not found"
        )
    
    try:
        rec_data = recommendations_store[recommendation_id]
        
        # Convert to ProductRecommendation object
        rec = ProductRecommendation(
            product_name=rec_data["product_name"],
            confidence=rec_data["confidence"],
            reasoning=rec_data["reasoning"],
            source_topics=rec_data["source_topics"],
            proposed_output_topic=rec_data["proposed_output_topic"],
            proposed_schema=rec_data["proposed_schema"],
            flink_sql=rec_data["flink_sql"],
            business_value=rec_data["business_value"],
            estimated_consumers=rec_data.get("estimated_consumers", 0),
            priority=rec_data.get("priority", "MEDIUM")
        )
        
        # Use AI to refine
        refined = recommender_agent.refine_recommendation(rec, request.user_feedback)
        
        # Update store
        recommendations_store[recommendation_id] = refined.to_dict()
        
        print(f"✅ Refined recommendation: {recommendation_id}")
        
        return refined.to_dict()
        
    except Exception as e:
        print(f"❌ Refinement failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to refine recommendation: {str(e)}"
        )


@app.post(
    "/recommendations/{recommendation_id}/approve",
    tags=["AI Recommendations"]
)
async def approve_recommendation(
    recommendation_id: str,
    request: ApprovalRequest
):
    """Approve a recommendation (Phase 2 will deploy Flink job)"""
    
    if recommendation_id not in recommendations_store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Recommendation {recommendation_id} not found"
        )
    
    rec = recommendations_store[recommendation_id]
    
    if request.modifications:
        for key, value in request.modifications.items():
            if key in rec:
                rec[key] = value
    
    rec["status"] = "APPROVED"
    rec["approved_by"] = request.approved_by
    rec["approved_at"] = datetime.utcnow().isoformat()
    
    recommendations_store[recommendation_id] = rec
    
    print(f"✅ Approved recommendation: {recommendation_id}")
    
    if request.deploy_immediately:
        print(f"⚠️  Deployment not yet implemented (Phase 2: Flink Integration)")
        
        return {
            "status": "approved",
            "recommendation_id": recommendation_id,
            "deployment_status": "pending",
            "message": "Recommendation approved. Flink deployment coming in Phase 2."
        }
    
    return {
        "status": "approved",
        "recommendation_id": recommendation_id,
        "message": "Recommendation approved successfully"
    }


@app.post(
    "/recommendations/{recommendation_id}/reject",
    tags=["AI Recommendations"]
)
async def reject_recommendation(
    recommendation_id: str,
    reason: str
):
    """Reject a recommendation"""
    
    if recommendation_id not in recommendations_store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Recommendation {recommendation_id} not found"
        )
    
    rec = recommendations_store[recommendation_id]
    rec["status"] = "REJECTED"
    rec["rejection_reason"] = reason
    rec["rejected_at"] = datetime.utcnow().isoformat()
    
    recommendations_store[recommendation_id] = rec
    
    print(f"✅ Rejected recommendation: {recommendation_id}")
    
    return {
        "status": "rejected",
        "recommendation_id": recommendation_id,
        "message": "Recommendation rejected"
    }


@app.get("/recommendations/stats", tags=["AI Recommendations"])
async def get_recommendation_stats():
    """Get statistics about AI recommendations"""
    
    total = len(recommendations_store)
    
    by_status = {}
    by_priority = {}
    total_confidence = 0
    
    for rec in recommendations_store.values():
        status_key = rec["status"]
        by_status[status_key] = by_status.get(status_key, 0) + 1
        
        priority = rec["priority"]
        by_priority[priority] = by_priority.get(priority, 0) + 1
        
        total_confidence += rec["confidence"]
    
    avg_confidence = total_confidence / total if total > 0 else 0
    
    return {
        "total_recommendations": total,
        "by_status": by_status,
        "by_priority": by_priority,
        "average_confidence": round(avg_confidence, 2),
        "high_confidence_count": len([
            r for r in recommendations_store.values()
            if r["confidence"] >= 0.8
        ])
    }


# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("DISCOVERY_AGENT_PORT", 8004))
    
    print(f"🚀 Starting Enhanced Catalog API on port {port}")
    print(f"📖 API docs: http://localhost:{port}/docs")
    
    uvicorn.run(
        "catalog_api:app",
        host="0.0.0.0",
        port=port,
        reload=True
    )