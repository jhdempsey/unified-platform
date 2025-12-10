"""ML Consumer - Processes order events through multiple ML models."""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from confluent_kafka import Consumer, KafkaError, Producer

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ml.models.demand_forecasting.model import DemandForecastingModel
from ml.models.inventory_optimization.model import InventoryOptimizationModel
from ml.models.supplier_reliability.model import SupplierReliabilityModel


class MLConsumer:
    """Consumes order events, runs ML predictions, produces results."""

    def __init__(self, bootstrap_servers: Optional[str] = None):
        # Get from environment or use default
        if bootstrap_servers is None:
            bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")

        # Consumer config
        self.consumer_config = {
            "bootstrap.servers": bootstrap_servers,
            "group.id": "ml-consumer-group",
            "auto.offset.reset": "earliest",
            "enable.auto.commit": False,
        }
        self.consumer = Consumer(self.consumer_config)

        # Producer config
        self.producer_config = {
            "bootstrap.servers": bootstrap_servers,
            "client.id": "ml-producer",
            "acks": "all",
            "enable.idempotence": True,
        }
        self.producer = Producer(self.producer_config)

        # Topics
        self.input_topic = "supply-chain.orders"
        self.prediction_topic = "supply-chain.predictions"
        self.alert_topic = "supply-chain.alerts"

        # Load ML models
        print("🤖 Loading ML models...")
        self.demand_model = DemandForecastingModel()
        self.supplier_model = SupplierReliabilityModel()
        self.inventory_model = InventoryOptimizationModel()
        print("✅ Loaded 3 models: Demand, Supplier, Inventory")

        self.stats = {"processed": 0, "predictions": 0, "alerts": 0, "errors": 0}

    def predict_order_risk(self, order: Dict[str, Any]) -> Dict[str, Any]:
        """Predict delivery risk for an order."""
        risk_score = 0.0

        # Factor 1: Supplier reliability
        risk_score += (1 - order["supplier"]["reliability"]) * 0.4

        # Factor 2: Delivery time vs perishability
        if order["product"]["perishable"]:
            shelf_life = order["product"]["shelf_life_days"]
            delivery_days = order["delivery_days"]
            if delivery_days > shelf_life * 0.5:
                risk_score += 0.3

        # Factor 3: Distance
        if order["distance_miles"] > 2000:
            risk_score += 0.2

        # Factor 4: Weather risk
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

    def process_order(self, order: Dict[str, Any]) -> Dict[str, Any]:
        """Process order through all ML models."""

        # Model 1: Order Risk
        risk_prediction = self.predict_order_risk(order)

        # Model 2: Supplier Reliability
        supplier_features = {
            "supplier_id": order["supplier"]["id"],
            "historical_reliability": order["supplier"]["reliability"],
            "region": order["supplier"]["region"],
            "distance_miles": order["distance_miles"],
        }
        supplier_prediction = self.supplier_model.predict(supplier_features)

        # Model 3: Inventory Optimization
        inventory_features = {
            "product_name": order["product"]["name"],
            "current_stock": order["quantity"],
            "daily_demand": order["quantity"] / order["delivery_days"],
            "lead_time_days": order["delivery_days"],
            "perishable": order["product"]["perishable"],
            "shelf_life_days": order["product"]["shelf_life_days"],
        }
        inventory_prediction = self.inventory_model.predict(inventory_features)

        # Create comprehensive prediction result
        prediction = {
            "order_id": order["order_id"],
            "timestamp": datetime.now().isoformat(),
            "tenant_id": order["tenant_id"],
            "predictions": {
                "order_risk": risk_prediction,
                "supplier_reliability": supplier_prediction,
                "inventory_optimization": inventory_prediction,
            },
            "metadata": {
                "product": order["product"]["name"],
                "supplier": order["supplier"]["name"],
                "delivery_days": order["delivery_days"],
                "quantity": order["quantity"],
            },
        }

        return prediction

    def should_alert(self, prediction: Dict[str, Any]) -> bool:
        """Determine if an alert should be triggered."""
        risk = prediction["predictions"]["order_risk"]
        supplier = prediction["predictions"]["supplier_reliability"]
        inventory = prediction["predictions"]["inventory_optimization"]

        # Alert on high risk OR poor supplier OR stockout risk
        return bool(  # Add bool() wrapper
            risk["risk_level"] == "high"
            or supplier["category"] == "poor"
            or inventory["stockout_risk"] == "high"
        )

    def create_alert(
        self, order: Dict[str, Any], prediction: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create alert for problematic order."""
        risk = prediction["predictions"]["order_risk"]
        supplier = prediction["predictions"]["supplier_reliability"]
        inventory = prediction["predictions"]["inventory_optimization"]

        # Determine primary issue
        issues = []
        if risk["risk_level"] == "high":
            issues.append("High delivery risk")
        if supplier["category"] in ["poor", "fair"]:
            issues.append(f"Supplier reliability: {supplier['category']}")
        if inventory["stockout_risk"] == "high":
            issues.append("Stockout risk")

        product_name = order["product"]["name"]
        supplier_name = order["supplier"]["name"]
        message = f"Risk detected: {product_name} from {supplier_name}"

        alert = {
            "alert_id": f"ALERT-{order['order_id']}",
            "timestamp": datetime.now().isoformat(),
            "order_id": order["order_id"],
            "severity": "high" if len(issues) > 1 else "medium",
            "alert_type": "supply_chain_risk",
            "message": message,
            "details": {
                "issues": issues,
                "risk_score": risk["risk_score"],
                "supplier_score": supplier["reliability_score"],
                "days_of_stock": inventory.get("days_of_stock", 0),
                "product": order["product"]["name"],
                "supplier": order["supplier"]["name"],
            },
            "recommended_actions": [],
        }

        # Add specific recommendations
        if risk["risk_level"] == "high":
            alert["recommended_actions"].extend(["Expedite shipping", "Track closely"])
        if supplier["category"] in ["poor", "fair"]:
            alert["recommended_actions"].append("Consider alternative supplier")
        if inventory["action"] == "reorder":
            qty = inventory["recommended_order_quantity"]
            alert["recommended_actions"].append(f"Reorder {qty} units")

        return alert

    def delivery_report(self, err, msg):
        """Callback for message delivery."""
        if err is not None:
            self.stats["errors"] += 1

    def run(self):
        """Main consumer loop."""
        self.consumer.subscribe([self.input_topic])

        print("\n🎯 ML Consumer started")
        print(f"📥 Input: {self.input_topic}")
        outputs = f"{self.prediction_topic}, {self.alert_topic}"
        print(f"📤 Outputs: {outputs}")
        print("🤖 Models: Order Risk, Supplier Reliability, Inventory")
        print("=" * 80)
        print()

        try:
            while True:
                msg = self.consumer.poll(timeout=1.0)

                if msg is None:
                    continue

                if msg.error():
                    if msg.error().code() != KafkaError._PARTITION_EOF:
                        print(f"❌ Consumer error: {msg.error()}")
                    continue

                try:
                    order = json.loads(msg.value().decode("utf-8"))
                    prediction = self.process_order(order)

                    # Produce prediction
                    self.producer.produce(
                        topic=self.prediction_topic,
                        key=order["order_id"].encode("utf-8"),
                        value=json.dumps(prediction).encode("utf-8"),
                        callback=self.delivery_report,
                    )
                    self.stats["predictions"] += 1

                    # Check for alerts
                    if self.should_alert(prediction):
                        alert = self.create_alert(order, prediction)
                        self.producer.produce(
                            topic=self.alert_topic,
                            key=alert["alert_id"].encode("utf-8"),
                            value=json.dumps(alert).encode("utf-8"),
                            callback=self.delivery_report,
                        )
                        self.stats["alerts"] += 1
                        print(f"🚨 {alert['message']}")

                    self.consumer.commit(asynchronous=False)
                    self.stats["processed"] += 1

                    if self.stats["processed"] % 10 == 0:
                        processed = self.stats["processed"]
                        predictions = self.stats["predictions"]
                        alerts = self.stats["alerts"]
                        print(
                            f"📊 Processed: {processed} | "
                            f"Predictions: {predictions} | "
                            f"Alerts: {alerts}"
                        )

                    self.producer.poll(0)

                except Exception as e:
                    print(f"❌ Error: {e}")
                    self.stats["errors"] += 1

        except KeyboardInterrupt:
            processed = self.stats["processed"]
            predictions = self.stats["predictions"]
            alerts = self.stats["alerts"]
            print(
                f"\n\n⏹️  Stopped | Processed: {processed} | "
                f"Predictions: {predictions} | Alerts: {alerts}"
            )
        finally:
            self.consumer.close()
            self.producer.flush()


if __name__ == "__main__":
    consumer = MLConsumer()
    consumer.run()
