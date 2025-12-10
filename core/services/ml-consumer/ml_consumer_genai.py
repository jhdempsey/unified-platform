"""ML Consumer with GenAI explanations."""

import asyncio
import json
import os
import sys
from pathlib import Path

from confluent_kafka import Consumer, KafkaError
from prometheus_client import Counter, Histogram, start_http_server

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ml.models.demand_forecasting.model import DemandForecastingModel
from ml.models.inventory_optimization.model import InventoryOptimizationModel
from ml.models.supplier_reliability.model import SupplierReliabilityModel
from services.genai_service import GenAIService

# Prometheus metrics
predictions_total = Counter(
    "ml_predictions_total", "Total predictions", ["model", "tenant"]
)
genai_explanations_total = Counter(
    "genai_explanations_total", "Total GenAI explanations", ["use_case"]
)
genai_latency = Histogram(
    "genai_explanation_latency_seconds", "GenAI explanation latency"
)
processing_latency = Histogram(
    "event_processing_latency_seconds", "Event processing latency"
)


class MLConsumerWithGenAI:
    """ML Consumer with GenAI-powered explanations."""

    def __init__(self):
        self.consumer = Consumer(
            {
                "bootstrap.servers": os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092"),
                "group.id": "ml-consumer-genai",
                "auto.offset.reset": "latest",
            }
        )

        self.consumer.subscribe(["order-events", "supplier-events", "inventory-events"])

        # ML Models
        self.models = {
            "demand_forecasting": DemandForecastingModel(),
            "inventory_optimization": InventoryOptimizationModel(),
            "supplier_reliability": SupplierReliabilityModel(),
        }

        # GenAI Service
        self.genai = None
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    async def initialize_genai(self):
        """Initialize GenAI service."""
        self.genai = GenAIService()

    def run(self):
        """Run the consumer with GenAI integration."""
        print("🚀 Starting ML Consumer with GenAI explanations...")

        # Initialize GenAI
        self.loop.run_until_complete(self.initialize_genai())

        # Start Prometheus metrics server
        start_http_server(9090)
        print("📊 Metrics available at http://localhost:9090/metrics")

        try:
            while True:
                msg = self.consumer.poll(1.0)

                if msg is None:
                    continue

                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        continue
                    else:
                        print(f"❌ Consumer error: {msg.error()}")
                        continue

                # Process message
                self.loop.run_until_complete(self.process_message(msg))

        except KeyboardInterrupt:
            print("\n⏹️  Shutting down...")
        finally:
            self.loop.run_until_complete(self.genai.close())
            self.consumer.close()
            self.loop.close()

    async def process_message(self, msg):
        """Process Kafka message with ML + GenAI."""

        try:
            event_data = json.loads(msg.value().decode("utf-8"))
            topic = msg.topic()

            print(f"\n📨 Processing {topic} event...")

            if topic == "order-events":
                await self.process_order_event(event_data)
            elif topic == "supplier-events":
                await self.process_supplier_event(event_data)
            elif topic == "inventory-events":
                await self.process_inventory_event(event_data)

        except Exception as e:
            print(f"❌ Error processing message: {e}")

    async def process_order_event(self, event: dict):
        """Process order event with risk explanation."""

        # 1. ML Prediction
        features = {
            "order_value": event.get("order_value", 0),
            "supplier_name": event.get("supplier_name", "Unknown"),
            "delivery_days": event.get("delivery_days", 0),
            "past_issues": event.get("past_issues", 0),
        }

        # Mock prediction (replace with actual model)
        risk_score = min(
            1.0,
            features["order_value"] / 10000 * 0.3
            + features["past_issues"] * 0.2
            + (features["delivery_days"] > 30) * 0.3,
        )

        prediction = {
            "risk_score": risk_score,
            "confidence": 0.85,
            "model": "order_risk_v1",
        }

        predictions_total.labels(
            model="order_risk", tenant=event.get("tenant_id", "default")
        ).inc()

        print(f"🎯 Risk Score: {risk_score:.2f}")

        # 2. GenAI Explanation
        with genai_latency.time():
            explanation = await self.genai.explain_risk_prediction(prediction, features)

        genai_explanations_total.labels(use_case="risk_explanation").inc()

        print(f"💡 Explanation: {explanation}")

        # 3. Produce enriched event (would send to Kafka)
        _ = {
            **event,
            "ml_prediction": prediction,
            "genai_explanation": explanation,
        }  # noqa: F841

        print("✅ Enriched event ready for downstream consumers")

    async def process_supplier_event(self, event: dict):
        """Process supplier event with reliability analysis."""

        supplier_data = {
            "name": event.get("supplier_name", "Unknown"),
            "reliability_score": event.get("reliability_score", 0),
            "on_time_rate": event.get("on_time_rate", 0),
            "quality_score": event.get("quality_score", 0),
            "response_time_hours": event.get("response_time_hours", 0),
            "total_orders": event.get("total_orders", 0),
        }

        predictions_total.labels(
            model="supplier_reliability", tenant=event.get("tenant_id", "default")
        ).inc()

        print(f"🏭 Analyzing supplier: {supplier_data['name']}")

        # GenAI Analysis
        with genai_latency.time():
            analysis = await self.genai.analyze_supplier_reliability(supplier_data)

        genai_explanations_total.labels(use_case="supplier_analysis").inc()

        print(f"💡 Analysis:\n{analysis}")

    async def process_inventory_event(self, event: dict):
        """Process inventory event with anomaly explanation."""

        anomaly_data = {
            "product_name": event.get("product_name", "Unknown"),
            "expected_quantity": event.get("expected_quantity", 0),
            "actual_quantity": event.get("actual_quantity", 0),
            "variance_pct": event.get("variance_pct", 0),
            "days_since_restock": event.get("days_since_restock", 0),
            "avg_daily_usage": event.get("avg_daily_usage", 0),
        }

        # Check if anomaly exists
        if abs(anomaly_data["variance_pct"]) < 20:
            print("✅ No significant anomaly detected")
            return

        predictions_total.labels(
            model="inventory_anomaly", tenant=event.get("tenant_id", "default")
        ).inc()

        print(f"⚠️  Anomaly detected: {anomaly_data['variance_pct']:.1f}% variance")

        # GenAI Explanation
        with genai_latency.time():
            explanation = await self.genai.explain_inventory_anomaly(anomaly_data)

        genai_explanations_total.labels(use_case="anomaly_explanation").inc()

        print(f"💡 Explanation:\n{explanation}")


if __name__ == "__main__":
    consumer = MLConsumerWithGenAI()
    consumer.run()
