"""AI Gateway Service - Multi-provider LLM integration with smart routing."""

import hashlib
import json
import os
import time
from typing import Any, Dict, Optional

import redis.asyncio as redis
from cost_tracker import CostTracker
from fastapi import FastAPI, Header, HTTPException
from prometheus_client import Counter, Gauge, Histogram, generate_latest
from providers import ProviderManager, ProviderType
from pydantic import BaseModel, Field
from router import RoutingStrategy, SmartRouter
from starlette.responses import Response

app = FastAPI(
    title="AI Gateway",
    version="1.0.0",
    description="Multi-provider LLM gateway with smart routing and cost optimization",
)

# Initialize components
provider_manager = ProviderManager()
smart_router = SmartRouter(provider_manager)
cost_tracker = CostTracker()

# Redis connection (optional - degrades gracefully)
redis_client: Optional[redis.Redis] = None

# Prometheus metrics
requests_total = Counter(
    "ai_gateway_requests_total", "Total requests", ["provider", "status", "team"]
)
request_duration = Histogram(
    "ai_gateway_request_duration_seconds", "Request duration", ["provider"]
)
tokens_used = Counter(
    "ai_gateway_tokens_total", "Total tokens used", ["provider", "team", "type"]
)
cost_total = Counter(
    "ai_gateway_cost_dollars", "Total cost in dollars", ["provider", "team"]
)
cache_hits = Counter("ai_gateway_cache_hits_total", "Cache hits", ["team"])
cache_misses = Counter("ai_gateway_cache_misses_total", "Cache misses", ["team"])
active_requests = Gauge("ai_gateway_active_requests", "Active requests", ["provider"])


class CompletionRequest(BaseModel):
    """Request for LLM completion."""

    prompt: str = Field(..., description="The prompt to send to the LLM")
    team_id: str = Field(..., description="Team identifier for cost tracking")
    max_tokens: int = Field(default=1000, description="Maximum tokens to generate")
    temperature: float = Field(
        default=0.7, ge=0, le=2, description="Sampling temperature"
    )
    routing_strategy: Optional[RoutingStrategy] = Field(
        default=RoutingStrategy.COST_OPTIMIZED,
        description="Routing strategy: cost_optimized, latency_optimized, "
        "quality_optimized",
    )
    preferred_provider: Optional[ProviderType] = Field(
        default=None,
        description="Preferred provider (will use as primary if available)",
    )
    use_cache: bool = Field(default=True, description="Whether to use caching")
    stream: bool = Field(default=False, description="Stream the response")


class CompletionResponse(BaseModel):
    """Response from LLM completion."""

    text: str
    provider: str
    model: str
    tokens_used: Dict[str, int]
    cost: float
    latency_ms: float
    cached: bool = False
    request_id: str


@app.on_event("startup")
async def startup_event():
    """Initialize connections on startup."""
    global redis_client

    # Try to connect to Redis (optional)
    redis_url = os.getenv("REDIS_URL", "redis://redis:6379")
    try:
        redis_client = redis.from_url(redis_url, decode_responses=True)
        await redis_client.ping()
        print(f"✅ Connected to Redis at {redis_url}")
    except Exception as e:
        print(f"⚠️  Redis not available: {e}. Caching disabled.")
        redis_client = None


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    if redis_client:
        await redis_client.close()


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "AI Gateway",
        "version": "1.0.0",
        "providers": [p.value for p in ProviderType],
        "cache_enabled": redis_client is not None,
    }


@app.get("/health")
async def health():
    """Health check."""
    providers_status = {}
    for provider_type in ProviderType:
        try:
            provider = provider_manager.get_provider(provider_type)
            providers_status[provider_type.value] = (
                "healthy" if provider.is_available() else "unavailable"
            )
        except Exception as e:
            providers_status[provider_type.value] = f"error: {str(e)}"

    return {
        "status": "healthy",
        "cache": "enabled" if redis_client else "disabled",
        "providers": providers_status,
    }


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    return Response(content=generate_latest(), media_type="text/plain")


@app.post("/v1/completions", response_model=CompletionResponse)
async def create_completion(
    request: CompletionRequest, x_api_key: Optional[str] = Header(None)
):
    """Create a completion using the AI Gateway."""
    start_time = time.time()
    request_id = hashlib.sha256(
        f"{request.team_id}-{time.time()}".encode()
    ).hexdigest()[:16]

    # Check cache first
    cache_key = None
    if request.use_cache and redis_client:
        cache_key = _generate_cache_key(request)
        cached_response = await _get_from_cache(cache_key)
        if cached_response:
            cache_hits.labels(team=request.team_id).inc()
            # Return cached response with proper fields
            return CompletionResponse(
                text=cached_response["text"],
                provider=cached_response.get("provider", "cached"),
                model=cached_response["model"],
                tokens_used=cached_response["tokens_used"],
                cost=cached_response["cost"],
                latency_ms=0.0,
                cached=True,
                request_id=request_id,
            )
        cache_misses.labels(team=request.team_id).inc()

    # Route to best provider
    selected_provider = smart_router.route(
        strategy=request.routing_strategy, preferred_provider=request.preferred_provider
    )

    if not selected_provider:
        raise HTTPException(status_code=503, detail="No providers available")

    # Track active requests
    active_requests.labels(provider=selected_provider.value).inc()

    try:
        # Get provider client
        provider = provider_manager.get_provider(selected_provider)

        # Make request with fallback
        response = None
        providers_tried = []

        for attempt_provider in smart_router.get_fallback_chain(selected_provider):
            providers_tried.append(attempt_provider.value)
            try:
                provider = provider_manager.get_provider(attempt_provider)
                response = await provider.complete(
                    prompt=request.prompt,
                    max_tokens=request.max_tokens,
                    temperature=request.temperature,
                )
                selected_provider = attempt_provider  # Update to successful provider
                break
            except Exception as e:
                print(f"Provider {attempt_provider.value} failed: {e}")
                if attempt_provider == providers_tried[-1]:
                    raise
                continue

        if not response:
            raise HTTPException(status_code=500, detail="All providers failed")

        # Calculate metrics
        latency_ms = (time.time() - start_time) * 1000

        # Track metrics
        requests_total.labels(
            provider=selected_provider.value, status="success", team=request.team_id
        ).inc()

        request_duration.labels(provider=selected_provider.value).observe(
            time.time() - start_time
        )

        tokens_used.labels(
            provider=selected_provider.value, team=request.team_id, type="prompt"
        ).inc(response["tokens_used"]["prompt"])

        tokens_used.labels(
            provider=selected_provider.value, team=request.team_id, type="completion"
        ).inc(response["tokens_used"]["completion"])

        cost_total.labels(provider=selected_provider.value, team=request.team_id).inc(
            response["cost"]
        )

        # Track in cost tracker
        cost_tracker.track_request(
            team_id=request.team_id,
            provider=selected_provider.value,
            model=response["model"],
            tokens=response["tokens_used"],
            cost=response["cost"],
        )

        # Cache response
        if cache_key and redis_client:
            await _cache_response(
                cache_key,
                {
                    "text": response["text"],
                    "model": response["model"],
                    "tokens_used": response["tokens_used"],
                    "cost": response["cost"],
                    "provider": selected_provider.value,
                },
            )

        # Build response
        return CompletionResponse(
            text=response["text"],
            provider=selected_provider.value,
            model=response["model"],
            tokens_used=response["tokens_used"],
            cost=response["cost"],
            latency_ms=latency_ms,
            cached=False,
            request_id=request_id,
        )

    except Exception as e:
        requests_total.labels(
            provider=selected_provider.value, status="error", team=request.team_id
        ).inc()
        raise HTTPException(status_code=500, detail=str(e)) from e

    finally:
        active_requests.labels(provider=selected_provider.value).dec()


@app.get("/v1/costs/{team_id}")
async def get_team_costs(team_id: str):
    """Get cost summary for a team."""
    return cost_tracker.get_team_summary(team_id)


@app.get("/v1/costs")
async def get_all_costs():
    """Get cost summary for all teams."""
    return cost_tracker.get_all_summaries()


def _generate_cache_key(request: CompletionRequest) -> str:
    """Generate cache key from request."""
    cache_content = f"{request.prompt}:{request.max_tokens}:{request.temperature}"
    return hashlib.sha256(cache_content.encode()).hexdigest()


async def _get_from_cache(cache_key: str) -> Optional[Dict[str, Any]]:
    """Get response from cache."""
    if not redis_client:
        return None

    try:
        cached = await redis_client.get(f"ai_gateway:cache:{cache_key}")
        if cached:
            data = json.loads(cached)
            # Ensure required fields exist for cached responses
            if "provider" not in data:
                data["provider"] = "cached"
            if "latency_ms" not in data:
                data["latency_ms"] = 0.0
            return data
    except Exception as e:
        print(f"Cache read error: {e}")

    return None


async def _cache_response(cache_key: str, response: Dict[str, Any], ttl: int = 3600):
    """Cache response."""
    if not redis_client:
        return

    try:
        # Cache the full response including provider info
        cache_data = {
            "text": response["text"],
            "model": response["model"],
            "tokens_used": response["tokens_used"],
            "cost": response["cost"],
            "provider": response.get("provider", "unknown"),
            "latency_ms": 0.0,  # Cached responses have no latency
        }
        await redis_client.setex(
            f"ai_gateway:cache:{cache_key}", ttl, json.dumps(cache_data)
        )
    except Exception as e:
        print(f"Cache write error: {e}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8002)
