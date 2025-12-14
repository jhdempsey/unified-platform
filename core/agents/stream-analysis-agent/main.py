"""
Stream Analysis Agent
AI-powered real-time data quality monitoring with HTTP health endpoint for Cloud Run
"""

import os
import sys
import signal
import threading
import time
from datetime import datetime
from typing import List, Dict, Any, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from analyzer import StreamAnalyzer
from kafka_consumer import StreamConsumer
from alert_producer import AlertProducer


# ============================================================================
# FastAPI App
# ============================================================================

app = FastAPI(
    title="Stream Analysis Agent",
    description="AI-powered real-time data quality monitoring",
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
_agent: Optional['StreamAnalysisAgent'] = None
_consumer_thread: Optional[threading.Thread] = None
_running = False


class StreamAnalysisAgent:
    """
    Main agent that coordinates:
    - Consuming from Kafka topics
    - Analyzing data quality with AI
    - Producing quality alerts
    """

    def __init__(self):
        """Initialize agent components"""
        print("🤖 Initializing Stream Analysis Agent...")

        # Initialize components
        self.analyzer = StreamAnalyzer()
        self.consumer = StreamConsumer(
            group_id="stream-analysis-agent",
            auto_offset_reset="latest"  # Only analyze new messages
        )
        self.alert_producer = AlertProducer()

        # Topics to monitor
        self.topics = [
            "supplier-events",
            "order-events",
            "product-events"
        ]

        # Stats
        self.stats = {
            "batches_analyzed": 0,
            "messages_analyzed": 0,
            "alerts_produced": 0,
            "last_batch_time": None,
            "errors": 0
        }

        print("✅ Agent initialized")

    def on_batch_received(self, topic: str, messages: List[Dict[str, Any]]):
        """
        Callback when a batch of messages is received

        Args:
            topic: Source topic
            messages: List of deserialized messages
        """
        print(f"\n📊 Analyzing batch from {topic}: {len(messages)} messages")

        try:
            # Analyze batch
            analysis = self.analyzer.analyze_batch(messages, topic)

            # Update stats
            self.stats["batches_analyzed"] += 1
            self.stats["messages_analyzed"] += len(messages)
            self.stats["last_batch_time"] = datetime.utcnow().isoformat()

            # Print analysis
            print(f"   Quality Score: {analysis.get('quality_score', 'N/A')}")
            print(f"   Severity: {analysis.get('severity', 'N/A')}")
            print(f"   Issues: {len(analysis.get('issues_found', []))}")

            # Determine if alert needed
            if self.analyzer.should_alert(analysis):
                print(f"   🚨 Alert triggered!")

                # Produce alert
                product_id = f"PROD-{topic.upper()}"
                self.alert_producer.produce_alert(
                    product_id=product_id,
                    analysis=analysis,
                    topic=topic
                )
                self.stats["alerts_produced"] += 1

        except Exception as e:
            print(f"   ❌ Analysis error: {e}")
            self.stats["errors"] += 1

    def run_consumer_loop(self):
        """Run the consumer loop (for background thread)"""
        global _running
        
        print(f"📥 Subscribing to topics: {self.topics}")
        self.consumer.subscribe(self.topics)

        print("🔄 Starting consumer loop...")
        
        while _running:
            try:
                count = self.consumer.consume_batch(
                    callback=self.on_batch_received,
                    timeout_seconds=5.0
                )
                
                if count > 0:
                    print(f"✅ Processed {count} messages")
                    
            except Exception as e:
                print(f"❌ Consumer loop error: {e}")
                self.stats["errors"] += 1
                time.sleep(1)  # Brief pause on error

        print("⏹️ Consumer loop stopped")

    def close(self):
        """Close all connections"""
        self.consumer.close()
        self.alert_producer.close()
        print("👋 Agent closed")


# ============================================================================
# HTTP Endpoints
# ============================================================================

@app.on_event("startup")
async def startup():
    """Initialize agent and start consumer thread"""
    global _agent, _consumer_thread, _running
    
    print("🚀 Starting Stream Analysis Agent...")
    
    try:
        _agent = StreamAnalysisAgent()
        _running = True
        
        # Start consumer in background thread
        _consumer_thread = threading.Thread(
            target=_agent.run_consumer_loop,
            daemon=True
        )
        _consumer_thread.start()
        
        print("✅ Agent started, consumer running in background")
        
    except Exception as e:
        print(f"❌ Failed to start agent: {e}")
        _running = False


@app.on_event("shutdown")
async def shutdown():
    """Stop consumer and cleanup"""
    global _agent, _running
    
    print("🛑 Shutting down...")
    _running = False
    
    if _agent:
        _agent.close()
    
    print("👋 Shutdown complete")


@app.get("/")
async def root():
    """Service info"""
    return {
        "service": "Stream Analysis Agent",
        "version": "1.0.0",
        "description": "AI-powered real-time data quality monitoring",
        "endpoints": {
            "/health": "Health check",
            "/stats": "Processing statistics",
            "/topics": "Monitored topics"
        }
    }


@app.get("/health")
async def health():
    """Health check for Cloud Run"""
    global _agent, _running
    
    if _agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    return {
        "status": "healthy" if _running else "stopping",
        "service": "stream-analysis-agent",
        "timestamp": datetime.utcnow().isoformat(),
        "consumer_running": _running,
        "batches_analyzed": _agent.stats["batches_analyzed"],
        "messages_analyzed": _agent.stats["messages_analyzed"],
        "alerts_produced": _agent.stats["alerts_produced"]
    }


@app.get("/stats")
async def stats():
    """Get processing statistics"""
    global _agent
    
    if _agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    return {
        "stats": _agent.stats,
        "topics": _agent.topics,
        "running": _running
    }


@app.get("/topics")
async def topics():
    """Get monitored topics"""
    global _agent
    
    if _agent is None:
        return {"topics": [], "status": "agent not initialized"}
    
    return {
        "topics": _agent.topics,
        "status": "monitoring"
    }


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8080"))
    print(f"🚀 Starting Stream Analysis Agent on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
