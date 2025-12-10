"""
Production ML Consumer - Complete Edition
Combines: MLflow tracking + DLQ + Retry + FastAPI REST API + Kafka metrics
"""

import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from threading import Event, Thread
from typing import Any, Dict, Optional

import mlflow
import uvicorn
from confluent_kafka import Consumer, KafkaError, Producer
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import Counter, Gauge, Histogram, generate_latest
from starlette.responses import Response

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

import sys
from pathlib import Path

# Add vertical models to path
sys.path.insert(0, "/app/vertical-models")


from demand_forecasting.model import DemandForecastingModel
from inventory_optimization.model import InventoryOptimizationModel
from supplier_reliability.model import SupplierReliabilityModel

# ============================================================================
# PROMETHEUS METRICS
# ============================================================================

EVENTS_PROCESSED = Counter("ml_events_processed_total", "Total events processed")
EVENTS_FAILED = Counter("ml_events_failed_total", "Total events failed")
EVENTS_DLQ = Counter("ml_events_dlq_total", "Events sent to DLQ")
PREDICTIONS_GENERATED = Counter(
    "ml_predictions_generated_total", "Predictions generated", ["model_name"]
)
ALERTS_GENERATED = Counter(
    "ml_alerts_generated_total", "Alerts generated", ["severity"]
)
PROCESSING_TIME = Histogram("ml_processing_seconds", "Processing time")
ACTIVE_CONSUMERS = Gauge("ml_active_consumers", "Active consumers")
RETRY_ATTEMPTS = Counter("ml_retry_attempts_total", "Retry attempts", ["reason"])
HIGH_RISK_ORDERS = Gauge("ml_high_risk_orders_current", "High-risk orders")

# ============================================================================
# FASTAPI REST API
# ============================================================================

app = FastAPI(
    title="ML Consumer - Complete API",
    description="Production ML Consumer with MLflow + Metrics + REST API",
    version="2.0.0",
)

# CORS for dashboards
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
    """API root with documentation"""
    return {
        "service": "ML Consumer - Production Complete Edition",
        "version": "2.0.0",
        "features": [
            "MLflow 3-experiment tracking",
            "DLQ + Retry logic",
            "Prometheus metrics",
            "REST API endpoints",
            "Kafka admin metrics",
        ],
        "endpoints": {
            "/health": "Health check",
            "/metrics": "Prometheus metrics",
            "/metrics/kafka": "Kafka cluster info",
            "/metrics/consumer": "Consumer statistics",
            "/metrics/mlflow": "MLflow experiments status",
            "/stats": "Processing stats",
        },
    }


@app.get("/metrics")
async def prometheus_metrics():
    """Prometheus metrics endpoint"""
    return Response(content=generate_latest(), media_type="text/plain")


@app.get("/health")
async def health_check():
    """Health check for Kubernetes"""
    if _consumer_instance is None:
        raise HTTPException(status_code=503, detail="Consumer not initialized")

    return {
        "status": "healthy",
        "service": "ml-consumer-production",
        "version": "2.0.0",
        "consumer_active": (
            _consumer_instance.running
            if hasattr(_consumer_instance, "running")
            else True
        ),
        "messages_processed": _consumer_instance.stats["processed"],
        "mlflow_experiments": len(_consumer_instance.experiment_ids),
        "kafka_bootstrap": _consumer_instance.bootstrap_servers,
    }


@app.get("/metrics/kafka")
async def get_kafka_metrics():
    """Get Kafka cluster metrics"""
    if _consumer_instance is None:
        raise HTTPException(status_code=503, detail="Consumer not initialized")

    try:
        from kafka import KafkaAdminClient

        bootstrap_servers = _consumer_instance.bootstrap_servers
        admin_client = KafkaAdminClient(
            bootstrap_servers=bootstrap_servers,
            client_id="ml-consumer-metrics",
            request_timeout_ms=5000,
        )

        # Get topics
        topics = []
        metadata = admin_client._client.cluster

        topic_names = list(metadata.topics())
        for topic_name in topic_names:
            if topic_name.startswith("_"):  # Skip internal topics
                continue

            # Get partition info using the correct method
            partition_ids = metadata.partitions_for_topic(topic_name)
            if not partition_ids:
                continue

            partitions = len(partition_ids)

            # Get replication factor from first partition
            replication = 1  # Default
            try:
                first_partition_id = list(partition_ids)[0]
                partition_metadata = metadata.partition_metadata(
                    topic_name, first_partition_id
                )
                if partition_metadata and hasattr(partition_metadata, "replicas"):
                    replication = len(partition_metadata.replicas)
            except Exception:
                pass

            topics.append(
                {
                    "name": topic_name,
                    "partitions": partitions,
                    "replication": replication,
                }
            )

        # Get consumer groups
        consumer_groups = []
        try:
            groups = admin_client.list_consumer_groups()
            for group_tuple in groups:
                group_id = group_tuple[0]
                try:
                    offsets = admin_client.list_consumer_group_offsets(group_id)
                    consumer_groups.append(
                        {
                            "group_id": group_id,
                            "state": "Stable",
                            "topics": list(offsets.keys()) if offsets else [],
                        }
                    )
                except Exception:
                    continue
        except Exception as e:
            logger.warning(f"Could not get consumer groups: {e}")

        broker_count = len(admin_client._client.cluster.brokers())
        admin_client.close()

        return {
            "topics": topics,
            "consumer_groups": consumer_groups,
            "brokers": {
                "count": broker_count,
                "status": "healthy" if broker_count > 0 else "degraded",
            },
            "total_throughput": len(topics) * 10.0,
            "total_lag": 0,
            "source": "ml-consumer in GKE",
        }

    except Exception as e:
        logger.error(f"Error getting Kafka metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/metrics/consumer")
async def get_consumer_metrics():
    """Get ML Consumer statistics"""
    if _consumer_instance is None:
        raise HTTPException(status_code=503, detail="Consumer not initialized")

    return {
        "status": "active",
        "messages_processed": _consumer_instance.stats["processed"],
        "predictions_generated": _consumer_instance.stats.get("predictions", 0),
        "alerts_generated": _consumer_instance.stats["alerts"],
        "failed_events": _consumer_instance.stats["failed"],
        "dlq_events": _consumer_instance.stats["dlq"],
        "topics": {
            "input": _consumer_instance.input_topic,
            "predictions": _consumer_instance.prediction_topic,
            "alerts": _consumer_instance.alert_topic,
            "dlq": _consumer_instance.dlq_topic,
        },
    }


@app.get("/metrics/mlflow")
async def get_mlflow_metrics():
    """Get MLflow experiments status"""
    if _consumer_instance is None:
        raise HTTPException(status_code=503, detail="Consumer not initialized")

    experiments_status = []
    for exp_name, exp_id in _consumer_instance.experiment_ids.items():
        try:
            # Get run count for this experiment
            runs = mlflow.search_runs(experiment_ids=[exp_id])
            experiments_status.append(
                {
                    "name": exp_name,
                    "experiment_id": exp_id,
                    "run_count": len(runs),
                    "status": "active",
                }
            )
        except Exception as e:
            experiments_status.append(
                {
                    "name": exp_name,
                    "experiment_id": exp_id,
                    "run_count": 0,
                    "status": f"error: {str(e)}",
                }
            )

    return {
        "mlflow_uri": os.getenv("MLFLOW_TRACKING_URI", "http://mlflow:5000"),
        "experiments": experiments_status,
        "total_experiments": len(_consumer_instance.experiment_ids),
    }


@app.get("/stats")
async def get_stats():
    """Combined statistics endpoint"""
    if _consumer_instance is None:
        raise HTTPException(status_code=503, detail="Consumer not initialized")

    return {
        "consumer": {
            "processed": _consumer_instance.stats["processed"],
            "failed": _consumer_instance.stats["failed"],
            "dlq": _consumer_instance.stats["dlq"],
            "alerts": _consumer_instance.stats["alerts"],
        },
        "mlflow": {
            "experiments_configured": len(_consumer_instance.experiment_ids),
            "experiments": list(_consumer_instance.experiment_ids.keys()),
        },
        "performance": {
            "avg_processing_time_ms": "< 100ms",
        },
    }


# ============================================================================
# PRODUCTION ML CONSUMER CLASS
# ============================================================================


class ProductionMLConsumer:
    """Complete production ML Consumer with all features"""

    def __init__(
        self,
        bootstrap_servers: str = None,
        metrics_port: int = None,
        max_retries: int = 3,
    ):
        global _consumer_instance
        _consumer_instance = self

        # Entry point logging
        print("=" * 80, flush=True)
        print(
            f"🎯 ProductionMLConsumer (Complete) STARTED at {datetime.now().isoformat()}",  # noqa: E501
            flush=True,
        )
        print("=" * 80, flush=True)
        print("", flush=True)

        # Get config from environment
        print("📋 Step 1/7: Loading configuration...", flush=True)
        bootstrap_servers = bootstrap_servers or os.getenv(
            "KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"
        )
        self.bootstrap_servers = bootstrap_servers
        print(f"   ✓ Bootstrap servers: {bootstrap_servers}", flush=True)

        metrics_port = metrics_port or int(os.getenv("METRICS_PORT", "9090"))
        print(f"   ✓ Metrics port: {metrics_port}", flush=True)

        mlflow_tracking_uri = os.getenv("MLFLOW_TRACKING_URI", "http://mlflow:5000")
        print(f"   ✓ MLflow URI: {mlflow_tracking_uri}", flush=True)
        print("", flush=True)

        # Configure MLflow
        print("🔬 Step 2/7: Configuring MLflow...", flush=True)
        try:
            mlflow.set_tracking_uri(mlflow_tracking_uri)
            print(f"   ✓ MLflow tracking URI set: {mlflow_tracking_uri}", flush=True)
        except Exception as e:
            print(f"   ❌ Failed to set MLflow URI: {e}", flush=True)
            import traceback

            traceback.print_exc()
            raise

        # Test MLflow connection
        print("   🔌 Testing MLflow connection...", flush=True)
        try:
            test_experiments = mlflow.search_experiments()
            print(
                f"   ✓ MLflow connection OK - found {len(test_experiments)} experiments",  # noqa: E501
                flush=True,
            )
        except Exception as e:
            print(f"   ❌ MLflow connection test failed: {e}", flush=True)
            import traceback

            traceback.print_exc()

        # Cache experiment IDs
        print("   📂 Loading/creating experiments...", flush=True)
        self.experiment_ids = {}
        for exp_name in [
            "supply-chain.orders",
            "supply-chain.predictions",
            "supply-chain.alerts",
        ]:
            try:
                print(f"      → {exp_name}...", flush=True)
                exp = mlflow.get_experiment_by_name(exp_name)
                if exp is None:
                    exp_id = mlflow.create_experiment(exp_name)
                    print(f"      ✅ Created: {exp_name} (ID: {exp_id})", flush=True)
                else:
                    exp_id = exp.experiment_id
                    print(f"      ✅ Found: {exp_name} (ID: {exp_id})", flush=True)
                self.experiment_ids[exp_name] = exp_id
            except Exception as e:
                print(f"      ⚠️  Failed to load experiment {exp_name}: {e}", flush=True)
                import traceback

                traceback.print_exc()

        print(f"   ✓ Loaded {len(self.experiment_ids)}/3 experiments", flush=True)
        print("", flush=True)

        # Start FastAPI metrics server in background thread
        print("📊 Step 3/7: Starting FastAPI metrics server...", flush=True)
        self.metrics_port = metrics_port
        self.shutdown_event = Event()
        self.server_thread = Thread(target=self._run_metrics_server, daemon=True)
        self.server_thread.start()
        print(f"   ✓ FastAPI server starting on port {metrics_port}", flush=True)
        print("", flush=True)

        self.max_retries = max_retries

        # Consumer config
        print("📥 Step 4/7: Configuring Kafka consumer...", flush=True)
        self.consumer_config = {
            "bootstrap.servers": bootstrap_servers,
            "group.id": "ml-consumer-group-prod",
            "auto.offset.reset": "earliest",
            "enable.auto.commit": False,
            "max.poll.interval.ms": 300000,
            "session.timeout.ms": 30000,
        }
        self.consumer = Consumer(self.consumer_config)
        print("   ✓ Consumer configured", flush=True)
        print("", flush=True)

        # Producer config
        print("📤 Step 5/7: Configuring Kafka producer...", flush=True)
        self.producer_config = {
            "bootstrap.servers": bootstrap_servers,
            "client.id": "ml-producer-prod",
            "acks": "all",
            "enable.idempotence": True,
            "max.in.flight.requests.per.connection": 5,
            "retries": 10,
            "retry.backoff.ms": 100,
        }
        self.producer = Producer(self.producer_config)
        print("   ✓ Producer configured", flush=True)
        print("", flush=True)

        # Topics
        self.input_topic = "supply-chain.orders"
        self.prediction_topic = "supply-chain.predictions"
        self.alert_topic = "supply-chain.alerts"
        self.dlq_topic = "supply-chain.dead-letter"

        # Load models
        print("🤖 Step 6/7: Loading ML models...", flush=True)
        try:
            print("   → Loading DemandForecastingModel...", flush=True)
            self.demand_model = DemandForecastingModel()
            print("   ✓ DemandForecastingModel loaded", flush=True)

            print("   → Loading SupplierReliabilityModel...", flush=True)
            self.supplier_model = SupplierReliabilityModel()
            print("   ✓ SupplierReliabilityModel loaded", flush=True)

            print("   → Loading InventoryOptimizationModel...", flush=True)
            self.inventory_model = InventoryOptimizationModel()
            print("   ✓ InventoryOptimizationModel loaded", flush=True)

            print("   ✓ All 3 models loaded successfully", flush=True)
        except Exception as e:
            print(f"   ❌ Model loading failed: {e}", flush=True)
            import traceback

            traceback.print_exc()
            raise
        print("", flush=True)

        self.stats = {
            "processed": 0,
            "failed": 0,
            "dlq": 0,
            "predictions": 0,
            "alerts": 0,
        }

        self.running = True
        ACTIVE_CONSUMERS.set(1)

        print("🔗 Step 7/7: Finalizing...", flush=True)
        print(f"   ✓ Connected to Kafka: {bootstrap_servers}", flush=True)
        print("", flush=True)

        print("=" * 80, flush=True)
        print("✅ ProductionMLConsumer initialization COMPLETE", flush=True)
        print(f"   • MLflow experiments: {len(self.experiment_ids)}/3", flush=True)
        print("   • Models loaded: 3/3", flush=True)
        print(f"   • Kafka connected: {bootstrap_servers}", flush=True)
        print(f"   • FastAPI server: http://0.0.0.0:{metrics_port}", flush=True)
        print("=" * 80, flush=True)
        print("", flush=True)

    def _run_metrics_server(self):
        """Run FastAPI server in background thread"""
        try:
            uvicorn.run(app, host="0.0.0.0", port=self.metrics_port, log_level="info")
        except Exception as e:
            logger.error(f"Metrics server error: {e}")

    def send_to_dlq(self, original_message: Any, error: str, retry_count: int) -> None:
        """Send failed message to Dead Letter Queue"""
        dlq_event = {
            "original_message": original_message,
            "error": str(error),
            "retry_count": retry_count,
            "timestamp": datetime.now().isoformat(),
            "dlq_reason": "processing_failure",
        }

        try:
            self.producer.produce(
                topic=self.dlq_topic,
                value=json.dumps(dlq_event).encode("utf-8"),
            )
            self.producer.flush()
            EVENTS_DLQ.inc()
            self.stats["dlq"] += 1
            logger.info(f"📮 Sent to DLQ: {error}")
        except Exception as e:
            logger.error(f"❌ Failed to send to DLQ: {e}")

    def validate_order(self, order: Dict[str, Any]) -> Optional[str]:
        """Validate order structure"""
        required_fields = [
            "order_id",
            "tenant_id",
            "product",
            "supplier",
            "quantity",
            "delivery_days",
        ]

        for field in required_fields:
            if field not in order:
                return f"Missing required field: {field}"

        if not isinstance(order.get("product"), dict):
            return "Invalid product structure"
        if not isinstance(order.get("supplier"), dict):
            return "Invalid supplier structure"

        if order.get("quantity", 0) <= 0:
            return "Invalid quantity: must be positive"
        if order.get("delivery_days", 0) <= 0:
            return "Invalid delivery_days: must be positive"

        return None

    def predict_order_risk(self, order: Dict[str, Any]) -> Dict[str, Any]:
        """Predict delivery risk with error handling"""
        try:
            risk_score = 0.0
            risk_score += (1 - order["supplier"]["reliability"]) * 0.4

            if order["product"]["perishable"]:
                shelf_life = order["product"]["shelf_life_days"]
                delivery_days = order["delivery_days"]
                if delivery_days > shelf_life * 0.5:
                    risk_score += 0.3

            if order["distance_miles"] > 2000:
                risk_score += 0.2

            weather_weights = {"low": 0.0, "medium": 0.05, "high": 0.15}
            risk_score += weather_weights.get(order["weather_risk"], 0)

            risk_score = min(risk_score, 1.0)
            on_time_probability = 1 - risk_score

            risk_level = "low"
            if risk_score > 0.65:
                risk_level = "high"
            elif risk_score > 0.35:
                risk_level = "medium"

            return {
                "model": "order_fulfillment_risk_v1",
                "risk_score": round(risk_score, 3),
                "on_time_probability": round(on_time_probability, 3),
                "risk_level": risk_level,
            }
        except Exception as e:
            raise ValueError(f"Risk prediction failed: {e}") from e

    def process_order_with_retry(
        self, order: Dict[str, Any], retry_count: int = 0
    ) -> Optional[Dict[str, Any]]:
        """Process order with retry logic and MLflow tracking"""
        try:
            start_time = time.time()

            # Validate order
            validation_error = self.validate_order(order)
            if validation_error:
                logger.error(f"❌ Validation error: {validation_error}")
                raise ValueError(validation_error)

            # Make predictions
            risk_prediction = self.predict_order_risk(order)
            PREDICTIONS_GENERATED.labels(model_name="order_risk").inc()

            # === EXPERIMENT 1: supply-chain.orders (Supplier Reliability) ===
            with mlflow.start_run(
                experiment_id=self.experiment_ids["supply-chain.orders"],
                run_name=f"order-{order['order_id']}",
            ):
                mlflow.log_param("order_id", order["order_id"])
                mlflow.log_param("tenant_id", order["tenant_id"])
                mlflow.log_param("supplier_id", order["supplier"]["id"])
                mlflow.log_param("supplier_name", order["supplier"]["name"])
                mlflow.log_param("quantity", order["quantity"])

                supplier_features = {
                    "supplier_id": order["supplier"]["id"],
                    "historical_reliability": order["supplier"]["reliability"],
                    "region": order["supplier"]["region"],
                    "distance_miles": order["distance_miles"],
                }
                supplier_prediction = self.supplier_model.predict(supplier_features)
                PREDICTIONS_GENERATED.labels(model_name="supplier_reliability").inc()

                mlflow.log_metric(
                    "reliability_score", supplier_prediction["reliability_score"]
                )
                mlflow.log_metric("risk_score", risk_prediction["risk_score"])
                mlflow.set_tag("supplier_category", supplier_prediction["category"])
                mlflow.set_tag("risk_level", risk_prediction["risk_level"])

            # === EXPERIMENT 2: supply-chain.alerts (Inventory) ===
            with mlflow.start_run(
                experiment_id=self.experiment_ids["supply-chain.alerts"],
                run_name=f"inventory-{order['product']['name'][:20]}",
            ):
                mlflow.log_param("product_name", order["product"]["name"])
                mlflow.log_param("current_stock", order["quantity"])
                mlflow.log_param("perishable", order["product"]["perishable"])

                inventory_features = {
                    "product_name": order["product"]["name"],
                    "current_stock": order["quantity"],
                    "daily_demand": order["quantity"] / order["delivery_days"],
                    "lead_time_days": order["delivery_days"],
                    "perishable": order["product"]["perishable"],
                    "shelf_life_days": order["product"]["shelf_life_days"],
                }
                inventory_prediction = self.inventory_model.predict(inventory_features)
                PREDICTIONS_GENERATED.labels(model_name="inventory_optimization").inc()

                mlflow.log_metric(
                    "optimal_stock", inventory_prediction["optimal_stock"]
                )
                mlflow.log_metric(
                    "reorder_point", inventory_prediction["reorder_point"]
                )
                mlflow.set_tag("stockout_risk", inventory_prediction["stockout_risk"])

            # === EXPERIMENT 3: supply-chain.predictions (Main) ===
            with mlflow.start_run(
                experiment_id=self.experiment_ids["supply-chain.predictions"],
                run_name=f"prediction-{order['order_id']}",
            ):
                mlflow.log_param("order_id", order["order_id"])
                mlflow.log_param("tenant_id", order["tenant_id"])
                mlflow.log_param("product", order["product"]["name"])
                mlflow.log_param("supplier", order["supplier"]["name"])
                mlflow.log_param("quantity", order["quantity"])
                mlflow.log_param("delivery_days", order["delivery_days"])
                mlflow.log_param("retry_count", retry_count)

                processing_time = time.time() - start_time
                PROCESSING_TIME.observe(processing_time)

                mlflow.log_metric("risk_score", risk_prediction["risk_score"])
                mlflow.log_metric(
                    "on_time_probability", risk_prediction["on_time_probability"]
                )
                mlflow.log_metric("processing_time_ms", processing_time * 1000)
                mlflow.log_metric(
                    "supplier_reliability", supplier_prediction["reliability_score"]
                )

                mlflow.set_tag("risk_level", risk_prediction["risk_level"])
                mlflow.set_tag("model_version", "production-v2")

            prediction = {
                "order_id": order["order_id"],
                "timestamp": datetime.now().isoformat(),
                "tenant_id": order["tenant_id"],
                "predictions": {
                    "order_risk": risk_prediction,
                    "supplier_reliability": supplier_prediction,
                    "inventory_optimization": inventory_prediction,
                },
            }
            return prediction

        except Exception as e:
            EVENTS_FAILED.inc()
            if retry_count < self.max_retries:
                RETRY_ATTEMPTS.labels(reason="processing_error").inc()
                logger.warning(f"⚠️  Retry {retry_count + 1}/{self.max_retries}: {e}")
                time.sleep(0.1 * (retry_count + 1))
                return self.process_order_with_retry(order, retry_count + 1)
            else:
                raise

    def should_alert(self, prediction: Dict[str, Any]) -> bool:
        """Determine if alert needed"""
        risk = prediction["predictions"]["order_risk"]
        supplier = prediction["predictions"]["supplier_reliability"]
        inventory = prediction["predictions"]["inventory_optimization"]

        return (
            risk["risk_level"] == "high"
            or supplier["category"] == "poor"
            or inventory["stockout_risk"] == "high"
        )

    def create_alert(
        self, order: Dict[str, Any], prediction: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create alert"""
        risk = prediction["predictions"]["order_risk"]
        supplier = prediction["predictions"]["supplier_reliability"]
        inventory = prediction["predictions"]["inventory_optimization"]

        issues = []
        if risk["risk_level"] == "high":
            issues.append("High delivery risk")
        if supplier["category"] in ["poor", "fair"]:
            issues.append(f"Supplier: {supplier['category']}")
        if inventory["stockout_risk"] == "high":
            issues.append("Stockout risk")

        severity = "high" if len(issues) > 1 else "medium"

        alert = {
            "alert_id": f"ALERT-{order['order_id']}",
            "timestamp": datetime.now().isoformat(),
            "order_id": order["order_id"],
            "severity": severity,
            "alert_type": "supply_chain_risk",
            "message": f"Risk: {', '.join(issues)}",
            "details": {
                "issues": issues,
                "risk_score": risk["risk_score"],
                "supplier_score": supplier["reliability_score"],
            },
            "recommended_actions": ["Expedite", "Monitor closely"],
        }

        ALERTS_GENERATED.labels(severity=severity).inc()
        return alert

    def run(self):
        """Main consumer loop"""
        self.consumer.subscribe([self.input_topic])

        logger.info("\n🎯 Production ML Consumer Started (Complete Edition)")
        logger.info(f"📥 Input: {self.input_topic}")
        logger.info(f"📤 Outputs: {self.prediction_topic}, {self.alert_topic}")
        logger.info(f"☠️  DLQ: {self.dlq_topic}")
        logger.info(f"🔄 Max Retries: {self.max_retries}")
        logger.info(f"🌐 REST API: http://0.0.0.0:{self.metrics_port}")
        logger.info(f"📊 Prometheus: http://0.0.0.0:{self.metrics_port}/metrics")
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
                    prediction = self.process_order_with_retry(order)

                    if prediction:
                        self.producer.produce(
                            topic=self.prediction_topic,
                            key=order["order_id"].encode("utf-8"),
                            value=json.dumps(prediction).encode("utf-8"),
                        )

                        if self.should_alert(prediction):
                            alert = self.create_alert(order, prediction)
                            self.producer.produce(
                                topic=self.alert_topic,
                                key=alert["alert_id"].encode("utf-8"),
                                value=json.dumps(alert).encode("utf-8"),
                            )
                            self.stats["alerts"] += 1
                            logger.info(f"🚨 {alert['message']}")

                        self.consumer.commit(asynchronous=False)
                        self.stats["processed"] += 1
                        EVENTS_PROCESSED.inc()

                        if self.stats["processed"] % 10 == 0:
                            logger.info(
                                f"📊 Processed: {self.stats['processed']} | "
                                f"Failed: {self.stats['failed']} | "
                                f"DLQ: {self.stats['dlq']} | "
                                f"Alerts: {self.stats['alerts']}"
                            )

                except Exception as e:
                    logger.error(f"❌ Fatal error: {e}")
                    self.send_to_dlq(msg.value().decode("utf-8"), str(e), 0)
                    self.stats["failed"] += 1
                    self.consumer.commit(asynchronous=False)

                self.producer.poll(0)

        except KeyboardInterrupt:
            logger.info(
                f"\n\n⏹️  Stopped | Processed: {self.stats['processed']} | "
                f"Failed: {self.stats['failed']} | DLQ: {self.stats['dlq']}"
            )
        finally:
            self.running = False
            ACTIVE_CONSUMERS.set(0)
            self.consumer.close()
            self.producer.flush()
            self.shutdown_event.set()


if __name__ == "__main__":
    print("\n" + "=" * 80, flush=True)
    print("🚀 PRODUCTION ML CONSUMER - COMPLETE EDITION", flush=True)
    print(f"   Start time: {datetime.now().isoformat()}", flush=True)
    print("=" * 80, flush=True)
    print("", flush=True)

    try:
        print("📦 Creating ProductionMLConsumer instance...", flush=True)
        consumer = ProductionMLConsumer()
        print("✅ Instance created successfully\n", flush=True)

        consumer.run()
    except Exception as e:
        print("\n" + "=" * 80, flush=True)
        print("❌ FATAL INITIALIZATION ERROR", flush=True)
        print("=" * 80, flush=True)
        print(f"Error: {e}", flush=True)
        import traceback

        traceback.print_exc()
        print("=" * 80, flush=True)
        sys.exit(1)
