"""Order Event Producer - Generates supply chain order events."""

import json
import os
import random
import time
from datetime import datetime, timedelta
from typing import Any, Dict

from confluent_kafka import Producer


class OrderEventProducer:
    """Produces order events to Kafka."""

    def __init__(self, bootstrap_servers: str = None):
        # Read from environment variable or use default
        if bootstrap_servers is None:
            bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")

        self.config = {
            "bootstrap.servers": bootstrap_servers,
            "client.id": "order-producer",
            "acks": "all",
            "enable.idempotence": True,
        }
        self.producer = Producer(self.config)
        self.topic = "supply-chain.orders"

        print(f"🔗 Connecting to Kafka: {bootstrap_servers}")

    def delivery_report(self, err, msg):
        """Callback for message delivery reports."""
        if err is not None:
            print(f"❌ Message delivery failed: {err}")
        else:
            topic = msg.topic()
            partition = msg.partition()
            offset = msg.offset()
            print(f"✅ Message delivered to {topic} [{partition}] @ offset {offset}")

    def generate_order_event(self, order_id: int) -> Dict[str, Any]:
        """Generate a realistic supply chain order event."""

        products = [
            {
                "name": "Organic Tomatoes",
                "category": "Produce",
                "perishable": True,
                "shelf_life_days": 7,
            },
            {
                "name": "Fresh Salmon",
                "category": "Seafood",
                "perishable": True,
                "shelf_life_days": 3,
            },
            {
                "name": "Aged Cheddar",
                "category": "Dairy",
                "perishable": True,
                "shelf_life_days": 30,
            },
            {
                "name": "Whole Grain Bread",
                "category": "Bakery",
                "perishable": True,
                "shelf_life_days": 5,
            },
            {
                "name": "Olive Oil",
                "category": "Pantry",
                "perishable": False,
                "shelf_life_days": 365,
            },
        ]

        suppliers = [
            {
                "id": "SUP001",
                "name": "Fresh Farms Co",
                "reliability": 0.95,
                "region": "California",
            },
            {
                "id": "SUP002",
                "name": "Ocean Harvest",
                "reliability": 0.88,
                "region": "Alaska",
            },
            {
                "id": "SUP003",
                "name": "Dairy Valley",
                "reliability": 0.92,
                "region": "Wisconsin",
            },
            {
                "id": "SUP004",
                "name": "Artisan Bakers",
                "reliability": 0.78,
                "region": "Oregon",
            },
            {
                "id": "SUP005",
                "name": "Global Foods",
                "reliability": 0.85,
                "region": "International",
            },
        ]

        product = random.choice(products)
        supplier = random.choice(suppliers)
        quantity = random.randint(50, 500)

        delivery_days = random.randint(2, 10)
        deadline = datetime.now() + timedelta(days=delivery_days)
        delivery_deadline = deadline.isoformat()

        distance_miles = random.randint(100, 3000)
        weather_risk = random.choice(["low", "medium", "high"])

        is_urgent = product["perishable"] and delivery_days <= 3
        priority = "high" if is_urgent else "normal"

        event = {
            "order_id": f"ORD-{order_id:06d}",
            "timestamp": datetime.now().isoformat(),
            "tenant_id": "food-distributor-001",
            "product": product,
            "supplier": supplier,
            "quantity": quantity,
            "unit_price": round(random.uniform(2.5, 25.0), 2),
            "delivery_deadline": delivery_deadline,
            "delivery_days": delivery_days,
            "distance_miles": distance_miles,
            "weather_risk": weather_risk,
            "priority": priority,
        }

        return event

    def produce_event(self, event: Dict[str, Any]):
        """Produce an event to Kafka."""
        try:
            self.producer.produce(
                topic=self.topic,
                key=event["order_id"].encode("utf-8"),
                value=json.dumps(event).encode("utf-8"),
                callback=self.delivery_report,
            )
            self.producer.poll(0)
        except Exception as e:
            print(f"❌ Error producing event: {e}")

    def produce_batch(self, num_events: int = 10, delay_ms: int = 1000):
        """Produce a batch of events with delay."""
        print(f"\n🚀 Producing {num_events} order events...\n")

        for i in range(1, num_events + 1):
            event = self.generate_order_event(i)
            self.produce_event(event)

            if delay_ms > 0:
                time.sleep(delay_ms / 1000.0)

        print("\n⏳ Flushing remaining messages...")
        self.producer.flush()
        print(f"✅ All {num_events} events produced successfully!\n")


if __name__ == "__main__":
    # Read configuration from environment variables
    num_events = int(os.getenv("NUM_EVENTS", "20"))
    delay_ms = int(os.getenv("DELAY_MS", "500"))

    producer = OrderEventProducer()
    producer.produce_batch(num_events=num_events, delay_ms=delay_ms)
