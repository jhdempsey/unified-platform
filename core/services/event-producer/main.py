"""
Event Producer Service
HTTP API wrapper for the load generator with health endpoint for Cloud Run
"""

import os
import sys
import json
import threading
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from producer import OrderEventProducer

# ============================================================================
# FastAPI App
# ============================================================================

app = FastAPI(
    title="Event Producer Service",
    description="Produces test events to Kafka for the unified platform",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
_producer: Optional[OrderEventProducer] = None
_stats = {
    "events_produced": 0,
    "last_event_time": None,
    "running": False
}


def get_producer() -> OrderEventProducer:
    """Get or create producer instance"""
    global _producer
    if _producer is None:
        _producer = OrderEventProducer()
    return _producer


@app.on_event("startup")
async def startup():
    """Initialize producer on startup"""
    global _producer
    print("🚀 Starting Event Producer Service...")
    try:
        _producer = OrderEventProducer()
        print("✅ Producer initialized")
    except Exception as e:
        print(f"❌ Failed to initialize producer: {e}")


@app.on_event("shutdown")
async def shutdown():
    """Cleanup on shutdown"""
    global _producer
    if _producer:
        _producer.close()
        print("👋 Producer closed")


@app.get("/")
async def root():
    """Service info"""
    return {
        "service": "Event Producer",
        "version": "1.0.0",
        "description": "Produces test events to Kafka",
        "endpoints": {
            "/health": "Health check",
            "/produce": "Produce a single event",
            "/produce/{count}": "Produce multiple events",
            "/stats": "Production statistics"
        }
    }


@app.get("/health")
async def health():
    """Health check for Cloud Run"""
    producer = get_producer()
    return {
        "status": "healthy",
        "service": "event-producer",
        "timestamp": datetime.utcnow().isoformat(),
        "kafka_bootstrap": producer.bootstrap_servers,
        "topic": producer.topic,
        "events_produced": _stats["events_produced"]
    }


@app.get("/stats")
async def stats():
    """Get production statistics"""
    return {
        "events_produced": _stats["events_produced"],
        "last_event_time": _stats["last_event_time"],
        "running": _stats["running"]
    }


@app.post("/produce")
async def produce_one():
    """Produce a single event"""
    global _stats
    
    try:
        producer = get_producer()
        event = producer.generate_order_event(_stats["events_produced"] + 1)
        producer.produce_event(event)
        producer.flush()
        
        _stats["events_produced"] += 1
        _stats["last_event_time"] = datetime.utcnow().isoformat()
        
        return {
            "status": "produced",
            "event": event,
            "total_produced": _stats["events_produced"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/produce/{count}")
async def produce_many(count: int, background_tasks: BackgroundTasks):
    """Produce multiple events"""
    if count < 1 or count > 1000:
        raise HTTPException(status_code=400, detail="Count must be between 1 and 1000")
    
    def produce_batch():
        global _stats
        producer = get_producer()
        _stats["running"] = True
        
        for i in range(count):
            event = producer.generate_order_event(_stats["events_produced"] + 1)
            producer.produce_event(event)
            _stats["events_produced"] += 1
            _stats["last_event_time"] = datetime.utcnow().isoformat()
        
        producer.flush()
        _stats["running"] = False
        print(f"✅ Produced {count} events")
    
    background_tasks.add_task(produce_batch)
    
    return {
        "status": "started",
        "count": count,
        "message": f"Producing {count} events in background"
    }


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8080"))
    print(f"🚀 Starting Event Producer on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
