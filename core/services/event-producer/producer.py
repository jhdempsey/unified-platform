"""Order Event Producer - Generates supply chain order events."""

import json
import os
import random
import time
from datetime import datetime, timedelta
from typing import Any, Dict

from confluent_kafka import Producer


class OrderEventProducer:
    """Produces order events to Kafka with SASL_SSL support."""

    def __init__(self, bootstrap_servers: str = None):
        # Read from environment variable or use default
        if bootstrap_servers is None:
            bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")

        # Get SASL credentials from environment (for Confluent Cloud)
        security_protocol = os.getenv("KAFKA_SECURITY_PROTOCOL", "PLAINTEXT")
        sasl_mechanism = os.getenv("KAFKA_SASL_MECHANISM", "")
        sasl_username = os.getenv("KAFKA_SASL_USERNAME", "")
        sasl_password = os.getenv("KAFKA_SASL_PASSWORD", "")

        # Base config
        self.config = {
            "bootstrap.servers": bootstrap_servers,
            "client.id": "order-producer",
            "acks": "all",
            "enable.idempotence": True,
        }

        # Add SASL config if using SASL_SSL (Confluent Cloud)
        if security_protocol == "SASL_SSL":
            self.config.update({
                'security.protocol': security_protocol,
                'sasl.mechanism': sasl_mechanism,
                'sasl.username': sasl_username,
                'sasl.password': sasl_password,
            })
            print(f"🔐 Using SASL_SSL authentication to {bootstrap_servers}")
        else:
            print(f"🔓 Using PLAINTEXT connection to {bootstrap_servers}")

        self.producer = Producer(self.config)
        self.topic = "supply-chain.orders"
        self.bootstrap_servers = bootstrap_servers

        print(f"🔗 Connected to Kafka: {bootstrap_servers}")

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
                "name": "Steel Bolts M8",
                "category": "Hardware",
                "perishable": False,
                "shelf_life_days": 3650,
            },
            {
                "name": "Fresh Salmon Fillet",
                "category": "Seafood",
                "perishable": True,
                "shelf_life_days": 3,
            },
            {
                "name": "Industrial Lubricant",
                "category": "Chemicals",
                "perishable": False,
                "shelf_life_days": 365,
            },
            {
                "name": "Organic Milk",
                "category": "Dairy",
                "perishable": True,
                "shelf_life_days": 14,
            },
        ]

        suppliers = [
            {"id": "SUP-001", "name": "Fresh Farms Co", "region": "West", "reliability": 0.95},
            {"id": "SUP-002", "name": "Steel Masters", "region": "Midwest", "reliability": 0.88},
            {"id": "SUP-003", "name": "Ocean Fresh", "region": "East", "reliability": 0.92},
            {"id": "SUP-004", "name": "ChemCorp", "region": "South", "reliability": 0.85},
            {"id": "SUP-005", "name": "Dairy Direct", "region": "North", "reliability": 0.91},
        ]

        tenants = ["tenant-retail-001", "tenant-mfg-002", "tenant-food-003"]

        product = random.choice(products)
        supplier = random.choice(suppliers)
        tenant = random.choice(tenants)

        order_event = {
            "order_id": f"ORD-{order_id:06d}",
            "tenant_id": tenant,
            "timestamp": datetime.utcnow().isoformat(),
            "product": product,
            "supplier": supplier,
            "quantity": random.randint(10, 1000),
            "unit_price": round(random.uniform(1.0, 100.0), 2),
            "delivery_days": random.randint(1, 14),
            "distance_miles": random.randint(50, 3000),
            "weather_risk": random.choice(["low", "medium", "high"]),
            "priority": random.choice(["standard", "express", "critical"]),
        }

        return order_event

    def produce_event(self, event: Dict[str, Any]):
        """Produce an event to Kafka."""
        self.producer.produce(
            topic=self.topic,
            key=event["order_id"].encode("utf-8"),
            value=json.dumps(event).encode("utf-8"),
            callback=self.delivery_report,
        )
        self.producer.poll(0)

    def flush(self):
        """Flush all pending messages."""
        self.producer.flush()

    def close(self):
        """Close the producer."""
        self.flush()
        print("👋 Producer closed")
