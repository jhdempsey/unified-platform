"""
ML Consumer - Cloud Run Edition
Simplified version with mock models for production deployment
"""

import json
import logging
import os
import sys
import time
from datetime import datetime
from threading import Event, Thread
from typing import Any, Dict, Optional

import uvicorn
from confluent_kafka import Consumer, KafkaError, Producer
try:
    import redis
except ImportError:
    redis = None

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import Response

# Redis configuration
REDIS_HOST = os.getenv("REDIS_HOST", "")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
redis_client = None

def get_redis_client():
    """Get or create Redis client"""
    global redis_client
    if redis_client is None and REDIS_HOST:
        try:
            redis_client = redis.Redis(
                host=REDIS_HOST,
                port=REDIS_PORT,
                decode_responses=True,
                socket_connect_timeout=5
            )
            redis_client.ping()
            logger.info(f"✅ Connected to Redis at {REDIS_HOST}:{REDIS_PORT}")
        except Exception as e:
            logger.warning(f"⚠️ Redis connection failed: {e}")
            redis_client = None
    return redis_client

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# ============================================================================
# MOCK ML MODELS (simplified for Cloud Run deployment)
# ============================================================================

class MockDemandForecastingModel:
    """Mock demand forecasting model"""
    def predict(self, features: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "forecast": features.get("quantity", 100) * 1.1,
            "confidence": 0.85,
            "trend": "increasing"
        }


class MockSupplierReliabilityModel:
    """Mock supplier reliability model"""
    def predict(self, features: Dict[str, Any]) -> Dict[str, Any]:
        reliability = features.get("historical_reliability", 0.9)
        return {
            "reliability_score": reliability,
            "category": "excellent" if reliability > 0.9 else "good" if reliability > 0.8 else "fair",
            "risk_factors": []
        }


class MockInventoryOptimizationModel:
    """Mock inventory optimization model"""
    def predict(self, features: Dict[str, Any]) -> Dict[str, Any]:
        current_stock = features.get("current_stock", 100)
        daily_demand = features.get("daily_demand", 10)
        return {
            "optimal_stock": int(daily_demand * 14),
            "reorder_point": int(daily_demand * 7),
            "stockout_risk": "low" if current_stock > daily_demand * 7 else "high"
        }


# ============================================================================
# FASTAPI REST API
# ============================================================================

app = FastAPI(
    title="ML Consumer - Cloud Run Edition",
    description="ML Consumer with mock models for Confluent Cloud",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global consumer instance
_consumer_instance = None


@app.get("/")
async def root():
    """API root"""
    return {
        "service": "ML Consumer - Cloud Run Edition",
        "version": "2.0.0",
        "features": [
            "Mock ML predictions",
            "Kafka consumer with SASL_SSL",
            "REST API endpoints",
        ],
        "endpoints": {
            "/health": "Health check",
            "/stats": "Processing stats",
        },
    }


@app.get("/health")
async def health_check():
    """Health check for Cloud Run"""
    if _consumer_instance is None:
        return {
            "status": "starting",
            "service": "ml-consumer",
            "version": "2.0.0",
        }

    return {
        "status": "healthy",
        "service": "ml-consumer",
        "version": "2.0.0",
        "consumer_active": _consumer_instance.running,
        "messages_processed": _consumer_instance.stats["processed"],
        "kafka_bootstrap": _consumer_instance.bootstrap_servers[:50] + "...",
    }


@app.get("/stats")
async def get_stats():
    """Get processing statistics"""
    if _consumer_instance is None:
        return {"status": "not initialized"}

    return {
        "consumer": _consumer_instance.stats,
        "topics": {
            "input": _consumer_instance.input_topic,
            "predictions": _consumer_instance.prediction_topic,
            "alerts": _consumer_instance.alert_topic,
        },
    }


# ============================================================================
# ML CONSUMER CLASS
# ============================================================================


class MLConsumer:
    """ML Consumer with mock models for Cloud Run"""

    def __init__(self, metrics_port: int = None):
        global _consumer_instance
        _consumer_instance = self

        print("=" * 80)
        print(f"🎯 MLConsumer STARTED at {datetime.now().isoformat()}")
        print("=" * 80)

        # Get config from environment
        self.bootstrap_servers = os.getenv(
            "KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"
        )
        metrics_port = metrics_port or int(os.getenv("PORT", "8080"))

        # Get SASL credentials
        security_protocol = os.getenv("KAFKA_SECURITY_PROTOCOL", "PLAINTEXT")
        sasl_mechanism = os.getenv("KAFKA_SASL_MECHANISM", "")
        sasl_username = os.getenv("KAFKA_SASL_USERNAME", "")
        sasl_password = os.getenv("KAFKA_SASL_PASSWORD", "")

        # Base Kafka config
        kafka_config = {
            "bootstrap.servers": self.bootstrap_servers,
        }

        # Add SASL config if using SASL_SSL
        if security_protocol == "SASL_SSL":
            kafka_config.update({
                "security.protocol": security_protocol,
                "sasl.mechanism": sasl_mechanism,
                "sasl.username": sasl_username,
                "sasl.password": sasl_password,
            })
            print(f"🔐 Using SASL_SSL authentication")
        else:
            print(f"🔓 Using PLAINTEXT connection")

        print(f"📍 Bootstrap: {self.bootstrap_servers}")

        # Consumer config
        consumer_config = {
            **kafka_config,
            "group.id": "ml-consumer-group",
            "auto.offset.reset": "earliest",
            "enable.auto.commit": False,
        }
        self.consumer = Consumer(consumer_config)

        # Producer config
        producer_config = {
            **kafka_config,
            "client.id": "ml-producer",
            "acks": "all",
        }
        self.producer = Producer(producer_config)

        # Topics
        self.input_topic = "supply-chain.orders"
        self.prediction_topic = "supply-chain.predictions"
        self.alert_topic = "supply-chain.alerts"

        # Load mock models
        print("🤖 Loading mock ML models...")
        self.demand_model = MockDemandForecastingModel()
        self.supplier_model = MockSupplierReliabilityModel()
        self.inventory_model = MockInventoryOptimizationModel()
        print("✅ Models loaded")

        self.stats = {
            "processed": 0,
            "failed": 0,
            "predictions": 0,
            "alerts": 0,
        }

        self.running = True
        self.metrics_port = metrics_port

        # Start FastAPI in background
        self.server_thread = Thread(target=self._run_server, daemon=True)
        self.server_thread.start()

        print(f"✅ MLConsumer initialized")
        print(f"   📥 Input: {self.input_topic}")
        print(f"   📤 Output: {self.prediction_topic}")
        print(f"   🌐 API: http://0.0.0.0:{metrics_port}")
        print("=" * 80)

    def _run_server(self):
        """Run FastAPI server"""
        uvicorn.run(app, host="0.0.0.0", port=self.metrics_port, log_level="warning")

    def process_order(self, order: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process an order and generate predictions"""
        try:
            # Generate mock predictions
            supplier_features = {
                "supplier_id": order.get("supplier", {}).get("id", "unknown"),
                "historical_reliability": order.get("supplier", {}).get("reliability", 0.9),
            }
            supplier_pred = self.supplier_model.predict(supplier_features)

            inventory_features = {
                "current_stock": order.get("quantity", 100),
                "daily_demand": order.get("quantity", 100) / max(order.get("delivery_days", 7), 1),
            }
            inventory_pred = self.inventory_model.predict(inventory_features)

            # Calculate simple risk score
            risk_score = 0.0
            if order.get("supplier", {}).get("reliability", 1.0) < 0.85:
                risk_score += 0.3
            if order.get("weather_risk") == "high":
                risk_score += 0.2
            if order.get("distance_miles", 0) > 2000:
                risk_score += 0.2

            prediction = {
                "order_id": order.get("order_id"),
                "timestamp": datetime.now().isoformat(),
                "tenant_id": order.get("tenant_id"),
                "predictions": {
                    "risk_score": round(risk_score, 3),
                    "risk_level": "high" if risk_score > 0.5 else "medium" if risk_score > 0.25 else "low",
                    "supplier_reliability": supplier_pred,
                    "inventory_optimization": inventory_pred,
                },
            }

            self.stats["predictions"] += 1
            return prediction

        except Exception as e:
            logger.error(f"❌ Processing error: {e}")
            self.stats["failed"] += 1
            return None

    def should_alert(self, prediction: Dict[str, Any]) -> bool:
        """Check if alert needed"""
        preds = prediction.get("predictions", {})
        return (
            preds.get("risk_level") == "high" or
            preds.get("inventory_optimization", {}).get("stockout_risk") == "high"
        )

    def create_alert(self, order: Dict[str, Any], prediction: Dict[str, Any]) -> Dict[str, Any]:
        """Create alert"""
        return {
            "alert_id": f"ALERT-{order.get('order_id', 'unknown')}",
            "timestamp": datetime.now().isoformat(),
            "order_id": order.get("order_id"),
            "severity": "high",
            "message": f"High risk detected for order {order.get('order_id')}",
            "predictions": prediction.get("predictions"),
        }

    def run(self):
        """Main consumer loop"""
        self.consumer.subscribe([self.input_topic])

        logger.info(f"\n🎯 ML Consumer Started")
        logger.info(f"📥 Consuming from: {self.input_topic}")
        logger.info("=" * 80)

        try:
            while self.running:
                msg = self.consumer.poll(timeout=1.0)

                if msg is None:
                    continue

                if msg.error():
                    if msg.error().code() != KafkaError._PARTITION_EOF:
                        logger.error(f"❌ Consumer error: {msg.error()}")
                    continue

                try:
                    order = json.loads(msg.value().decode("utf-8"))
                    prediction = self.process_order(order)

                    if prediction:
                        # Produce prediction
                        self.producer.produce(
                            topic=self.prediction_topic,
                            key=order.get("order_id", "").encode("utf-8"),
                            value=json.dumps(prediction).encode("utf-8"),
                        )

                        # Check for alert
                        if self.should_alert(prediction):
                            alert = self.create_alert(order, prediction)
                            self.producer.produce(
                                topic=self.alert_topic,
                                key=alert["alert_id"].encode("utf-8"),
                                value=json.dumps(alert).encode("utf-8"),
                            )
                            self.stats["alerts"] += 1
                            logger.info(f"🚨 Alert: {alert['message']}")

                        self.consumer.commit(asynchronous=False)
                        self.stats["processed"] += 1

                        if self.stats["processed"] % 10 == 0:
                            logger.info(
                                f"📊 Processed: {self.stats['processed']} | "
                                f"Predictions: {self.stats['predictions']} | "
                                f"Alerts: {self.stats['alerts']}"
                            )

                except Exception as e:
                    logger.error(f"❌ Error processing message: {e}")
                    self.stats["failed"] += 1
                    self.consumer.commit(asynchronous=False)

                self.producer.poll(0)

        except KeyboardInterrupt:
            logger.info(f"\n⏹️ Stopped | Processed: {self.stats['processed']}")
        finally:
            self.running = False
            self.consumer.close()
            self.producer.flush()



@app.get("/cache/stats")
async def cache_stats():
    """Get Redis cache statistics"""
    r = get_redis_client()
    if not r:
        return {
            "status": "not_configured",
            "message": "Redis not configured or not connected"
        }
    try:
        info = r.info()
        return {
            "status": "connected",
            "used_memory": info.get("used_memory_human"),
            "connected_clients": info.get("connected_clients"),
            "total_commands_processed": info.get("total_commands_processed"),
            "keyspace_hits": info.get("keyspace_hits"),
            "keyspace_misses": info.get("keyspace_misses"),
            "keys": r.dbsize()
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/cache/prediction")
async def cache_prediction(key: str, value: dict):
    """Cache a prediction result"""
    r = get_redis_client()
    if not r:
        raise HTTPException(status_code=503, detail="Redis not available")
    try:
        r.setex(f"prediction:{key}", 3600, json.dumps(value))  # 1 hour TTL
        return {"status": "cached", "key": key}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/cache/prediction/{key}")
async def get_cached_prediction(key: str):
    """Get a cached prediction"""
    r = get_redis_client()
    if not r:
        raise HTTPException(status_code=503, detail="Redis not available")
    try:
        value = r.get(f"prediction:{key}")
        if value:
            return {"status": "hit", "key": key, "value": json.loads(value)}
        return {"status": "miss", "key": key}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    print("\n🚀 Starting ML Consumer - Cloud Run Edition")
    
    try:
        consumer = MLConsumer()
        consumer.run()
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
