"""
Kafka Event Producer for Product Service
Publishes product events to Kafka with Avro serialization
Supports SASL_SSL authentication for Confluent Cloud
"""

import os
import json
from typing import Optional
from confluent_kafka import Producer
from confluent_kafka.serialization import SerializationContext, MessageField
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroSerializer


class ProductEventProducer:
    """
    Produces product events to Kafka
    Supports both local (PLAINTEXT) and cloud (SASL_SSL) deployments
    """

    def __init__(
        self,
        bootstrap_servers: str = None,
        schema_registry_url: str = None
    ):
        """
        Initialize producer

        Args:
            bootstrap_servers: Kafka bootstrap servers
            schema_registry_url: Schema Registry URL
        """
        self.bootstrap_servers = bootstrap_servers or os.getenv(
            "KAFKA_BOOTSTRAP_SERVERS",
            "localhost:19093"
        )
        self.schema_registry_url = schema_registry_url or os.getenv(
            "SCHEMA_REGISTRY_URL",
            "http://localhost:18081"
        )

        # Get SASL credentials from environment (for Confluent Cloud)
        security_protocol = os.getenv("KAFKA_SECURITY_PROTOCOL", "PLAINTEXT")
        sasl_mechanism = os.getenv("KAFKA_SASL_MECHANISM", "")
        sasl_username = os.getenv("KAFKA_SASL_USERNAME", "")
        sasl_password = os.getenv("KAFKA_SASL_PASSWORD", "")

        # Base producer config
        producer_config = {
            'bootstrap.servers': self.bootstrap_servers,
            'client.id': 'product-service-producer',
            'acks': 'all',
        }

        # Add SASL config if using SASL_SSL (Confluent Cloud)
        if security_protocol == "SASL_SSL":
            producer_config.update({
                'security.protocol': security_protocol,
                'sasl.mechanism': sasl_mechanism,
                'sasl.username': sasl_username,
                'sasl.password': sasl_password,
            })
            print(f"🔐 Using SASL_SSL authentication to {self.bootstrap_servers}")
        else:
            print(f"🔓 Using PLAINTEXT connection to {self.bootstrap_servers}")

        # Initialize Kafka producer
        self.producer = Producer(producer_config)

        # Schema Registry config
        sr_config = {'url': self.schema_registry_url}
        
        # Add Schema Registry auth if available
        sr_api_key = os.getenv("SCHEMA_REGISTRY_API_KEY", "")
        sr_api_secret = os.getenv("SCHEMA_REGISTRY_API_SECRET", "")
        if sr_api_key and sr_api_secret:
            sr_config['basic.auth.user.info'] = f"{sr_api_key}:{sr_api_secret}"
            print(f"🔐 Using authenticated Schema Registry")

        # Initialize Schema Registry client
        try:
            self.schema_registry_client = SchemaRegistryClient(sr_config)
            print(f"✅ Connected to Schema Registry: {self.schema_registry_url}")
        except Exception as e:
            print(f"⚠️ Schema Registry connection failed: {e}")
            self.schema_registry_client = None

        # Product event schema
        self.product_schema = """
        {
            "type": "record",
            "name": "ProductEvent",
            "namespace": "com.supplychain.products",
            "fields": [
                {"name": "event_type", "type": "string"},
                {"name": "product_id", "type": "string"},
                {"name": "name", "type": "string"},
                {"name": "description", "type": ["null", "string"], "default": null},
                {"name": "owner_team", "type": "string"},
                {"name": "status", "type": "string"},
                {"name": "kafka_topic", "type": ["null", "string"], "default": null},
                {"name": "timestamp", "type": "string"}
            ]
        }
        """

        # Initialize Avro serializer if Schema Registry available
        if self.schema_registry_client:
            try:
                self.avro_serializer = AvroSerializer(
                    self.schema_registry_client,
                    self.product_schema
                )
            except Exception as e:
                print(f"⚠️ Avro serializer initialization failed: {e}")
                self.avro_serializer = None
        else:
            self.avro_serializer = None

        self.topic = "product-events"

    def _delivery_report(self, err, msg):
        """Callback for message delivery reports"""
        if err is not None:
            print(f"❌ Delivery failed: {err}")
        else:
            print(f"✅ Delivered to {msg.topic()} [{msg.partition()}]")

    def publish_product_event(self, event_type: str, product) -> bool:
        """
        Publish a product event

        Args:
            event_type: Type of event (created, updated, deleted)
            product: Product model instance

        Returns:
            True if published successfully
        """
        from datetime import datetime

        event = {
            "event_type": event_type,
            "product_id": product.id,
            "name": product.name,
            "description": product.description,
            "owner_team": product.owner_team,
            "status": product.status,
            "kafka_topic": product.kafka_topic,
            "timestamp": datetime.utcnow().isoformat()
        }

        try:
            if self.avro_serializer:
                # Serialize with Avro
                serialized = self.avro_serializer(
                    event,
                    SerializationContext(self.topic, MessageField.VALUE)
                )
                self.producer.produce(
                    topic=self.topic,
                    value=serialized,
                    key=product.id.encode('utf-8'),
                    callback=self._delivery_report
                )
            else:
                # Fall back to JSON
                self.producer.produce(
                    topic=self.topic,
                    value=json.dumps(event).encode('utf-8'),
                    key=product.id.encode('utf-8'),
                    callback=self._delivery_report
                )

            self.producer.poll(0)
            return True

        except Exception as e:
            print(f"❌ Failed to publish event: {e}")
            return False

    def flush(self, timeout: float = 10.0) -> int:
        """Flush pending messages"""
        remaining = self.producer.flush(timeout)
        if remaining > 0:
            print(f"⚠️ {remaining} messages still pending after flush")
        return remaining

    def close(self):
        """Close producer"""
        self.flush()
        print("👋 Producer closed")


# Singleton instance
_producer_instance: Optional[ProductEventProducer] = None


def get_event_producer() -> ProductEventProducer:
    """Get or create producer instance"""
    global _producer_instance
    if _producer_instance is None:
        _producer_instance = ProductEventProducer()
    return _producer_instance
