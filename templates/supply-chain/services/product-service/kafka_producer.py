"""
Kafka Producer for Product Events
Publishes product lifecycle events to Kafka
"""

import os
import uuid
from datetime import datetime
from typing import Dict, Any, Optional

from confluent_kafka import Producer
from confluent_kafka.serialization import SerializationContext, MessageField
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroSerializer

from models import DataProduct


class ProductEventProducer:
    """
    Produces product events to Kafka with Avro serialization
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
        
        # Initialize Schema Registry client
        self.schema_registry_client = SchemaRegistryClient({
            'url': self.schema_registry_url
        })
        
        # Initialize Kafka producer
        self.producer = Producer({
            'bootstrap.servers': self.bootstrap_servers,
            'client.id': f'product-service-{uuid.uuid4().hex[:8]}'
        })
        
        # Load and cache Avro schema
        self.serializer = self._load_serializer()
    
    def _load_serializer(self) -> AvroSerializer:
        """Load Avro serializer for product events"""
        # Avro schema for ProductCreatedEvent
        schema_str = """
        {
          "type": "record",
          "name": "ProductCreatedEvent",
          "namespace": "com.platform.events",
          "fields": [
            {"name": "event_id", "type": "string"},
            {"name": "product_id", "type": "string"},
            {"name": "product_name", "type": "string"},
            {"name": "product_type", "type": {"type": "enum", "name": "ProductType", "symbols": ["DATASET", "STREAM", "API", "REPORT", "ML_MODEL"]}},
            {"name": "owner", "type": "string"},
            {"name": "description", "type": ["null", "string"], "default": null},
            {"name": "schema_version", "type": "string", "default": "1.0.0"},
            {"name": "tags", "type": {"type": "array", "items": "string"}, "default": []},
            {"name": "quality_score", "type": ["null", "double"], "default": null},
            {"name": "kafka_topic", "type": ["null", "string"], "default": null},
            {"name": "timestamp", "type": "long", "logicalType": "timestamp-millis"},
            {"name": "created_by", "type": "string"},
            {"name": "extra_metadata", "type": {"type": "map", "values": "string"}, "default": {}}
          ]
        }
        """
        
        return AvroSerializer(
            self.schema_registry_client,
            schema_str
        )
    
    def produce_product_created(
        self,
        product: DataProduct,
        callback: Optional[callable] = None
    ):
        """
        Produce a product created event
        
        Args:
            product: Data product
            callback: Optional delivery callback
        """
        # Create event
        event = {
            "event_id": str(uuid.uuid4()),
            "product_id": product.product_id,
            "product_name": product.product_name,
            "product_type": product.product_type.value,
            "owner": product.owner,
            "description": product.description,
            "schema_version": product.schema_version,
            "tags": product.tags or [],
            "quality_score": product.quality_score,
            "kafka_topic": product.kafka_topic,
            "timestamp": int(datetime.utcnow().timestamp() * 1000),
            "created_by": product.created_by,
            "extra_metadata": {k: str(v) for k, v in (product.extra_metadata or {}).items()}
        }
        
        # Serialize
        serialized_value = self.serializer(
            event,
            SerializationContext("product-events", MessageField.VALUE)
        )
        
        # Produce
        self.producer.produce(
            topic="product-events",
            key=product.product_id.encode('utf-8'),
            value=serialized_value,
            on_delivery=callback or self._default_callback
        )
        
        # Trigger callbacks
        self.producer.poll(0)
    
    def produce_product_updated(
        self,
        product: DataProduct,
        callback: Optional[callable] = None
    ):
        """
        Produce a product updated event
        Similar to created but with updated fields
        """
        # For now, use same schema as created
        # In production, you might have a separate UpdatedEvent schema
        self.produce_product_created(product, callback)
    
    def flush(self, timeout: float = 10.0):
        """Flush pending messages"""
        remaining = self.producer.flush(timeout)
        if remaining > 0:
            print(f"⚠️  {remaining} messages still in queue after flush")
    
    @staticmethod
    def _default_callback(err, msg):
        """Default delivery callback"""
        if err:
            print(f"❌ Event delivery failed: {err}")
        else:
            print(f"✅ Event delivered to {msg.topic()} [{msg.partition()}] @ {msg.offset()}")
    
    def close(self):
        """Close producer"""
        self.flush()


# Singleton instance
_producer_instance: Optional[ProductEventProducer] = None


def get_event_producer() -> ProductEventProducer:
    """Get or create producer instance"""
    global _producer_instance
    if _producer_instance is None:
        _producer_instance = ProductEventProducer()
    return _producer_instance
