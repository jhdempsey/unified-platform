"""
Alert Producer
Produces quality alerts to Kafka
"""

import os
import uuid
from datetime import datetime
from typing import Dict, Any, Optional

from confluent_kafka import Producer
from confluent_kafka.serialization import SerializationContext, MessageField
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroSerializer


class AlertProducer:
    """
    Produces quality alert events to Kafka
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
            'client.id': f'alert-producer-{uuid.uuid4().hex[:8]}'
        })
        
        # Load serializer
        self.serializer = self._load_serializer()
    
    def _load_serializer(self) -> AvroSerializer:
        """Load Avro serializer for quality alerts"""
        schema_str = """
        {
          "type": "record",
          "name": "QualityAlertEvent",
          "namespace": "com.platform.events",
          "fields": [
            {"name": "event_id", "type": "string"},
            {"name": "alert_type", "type": {"type": "enum", "name": "AlertType", "symbols": ["ANOMALY", "MISSING_DATA", "SCHEMA_VIOLATION", "THRESHOLD_BREACH", "DATA_DRIFT"]}},
            {"name": "severity", "type": {"type": "enum", "name": "Severity", "symbols": ["LOW", "MEDIUM", "HIGH", "CRITICAL"]}},
            {"name": "product_id", "type": "string"},
            {"name": "topic_name", "type": ["null", "string"], "default": null},
            {"name": "description", "type": "string"},
            {"name": "ai_analysis", "type": ["null", "string"], "default": null},
            {"name": "affected_records", "type": "int", "default": 0},
            {"name": "sample_data", "type": ["null", "string"], "default": null},
            {"name": "metrics", "type": {"type": "map", "values": "double"}, "default": {}},
            {"name": "timestamp", "type": "long", "logicalType": "timestamp-millis"},
            {"name": "detection_method", "type": "string", "default": "AI_AGENT"},
            {"name": "metadata", "type": {"type": "map", "values": "string"}, "default": {}}
          ]
        }
        """
        
        return AvroSerializer(
            self.schema_registry_client,
            schema_str
        )
    
    def produce_alert(
        self,
        analysis: Dict[str, Any],
        topic: str,
        product_id: str = "UNKNOWN"
    ):
        """
        Produce a quality alert based on analysis results
        
        Args:
            analysis: Analysis results from StreamAnalyzer
            topic: Source topic that was analyzed
            product_id: Associated product ID
        """
        # Map analysis to alert type
        alert_type = "ANOMALY"
        if any("missing" in issue.lower() for issue in analysis.get("issues_found", [])):
            alert_type = "MISSING_DATA"
        elif any("schema" in issue.lower() for issue in analysis.get("issues_found", [])):
            alert_type = "SCHEMA_VIOLATION"
        
        # Create alert event
        event = {
            "event_id": str(uuid.uuid4()),
            "alert_type": alert_type,
            "severity": analysis.get("severity", "MEDIUM"),
            "product_id": product_id,
            "topic_name": topic,
            "description": analysis.get("summary", "Data quality issue detected"),
            "ai_analysis": "\n".join(analysis.get("recommendations", [])),
            "affected_records": analysis.get("analyzed_messages", 0),
            "sample_data": None,
            "metrics": {
                "quality_score": float(analysis.get("quality_score", 0)),
                "analyzed_messages": float(analysis.get("analyzed_messages", 0))
            },
            "timestamp": int(datetime.utcnow().timestamp() * 1000),
            "detection_method": analysis.get("analysis_method", "AI_AGENT"),
            "metadata": {
                "source_topic": topic,
                "issues_count": str(len(analysis.get("issues_found", [])))
            }
        }
        
        # Serialize
        serialized_value = self.serializer(
            event,
            SerializationContext("quality-alerts", MessageField.VALUE)
        )
        
        # Produce
        self.producer.produce(
            topic="quality-alerts",
            key=product_id.encode('utf-8'),
            value=serialized_value,
            on_delivery=self._delivery_callback
        )
        
        # Trigger callbacks
        self.producer.poll(0)
    
    def flush(self, timeout: float = 10.0):
        """Flush pending messages"""
        remaining = self.producer.flush(timeout)
        if remaining > 0:
            print(f"⚠️  {remaining} alerts still in queue")
    
    @staticmethod
    def _delivery_callback(err, msg):
        """Delivery callback"""
        if err:
            print(f"❌ Alert delivery failed: {err}")
        else:
            print(f"✅ Alert delivered to {msg.topic()} [{msg.partition()}] @ {msg.offset()}")
    
    def close(self):
        """Close producer"""
        self.flush()
