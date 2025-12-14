"""
Alert Producer for Stream Analysis
Produces quality alerts to Kafka with SASL_SSL support
"""

import os
import json
from datetime import datetime
from typing import Dict, Any, Optional

from confluent_kafka import Producer


class AlertProducer:
    """
    Produces data quality alerts to Kafka
    Supports SASL_SSL authentication for Confluent Cloud
    """

    def __init__(self, bootstrap_servers: str = None):
        """
        Initialize alert producer

        Args:
            bootstrap_servers: Kafka bootstrap servers
        """
        self.bootstrap_servers = bootstrap_servers or os.getenv(
            "KAFKA_BOOTSTRAP_SERVERS",
            "localhost:19093"
        )

        # Get SASL credentials from environment (for Confluent Cloud)
        security_protocol = os.getenv("KAFKA_SECURITY_PROTOCOL", "PLAINTEXT")
        sasl_mechanism = os.getenv("KAFKA_SASL_MECHANISM", "")
        sasl_username = os.getenv("KAFKA_SASL_USERNAME", "")
        sasl_password = os.getenv("KAFKA_SASL_PASSWORD", "")

        # Base producer config
        producer_config = {
            'bootstrap.servers': self.bootstrap_servers,
            'client.id': 'stream-analysis-alerts',
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
            print(f"🔐 Alert producer using SASL_SSL authentication")
        else:
            print(f"🔓 Alert producer using PLAINTEXT connection")

        self.producer = Producer(producer_config)
        self.topic = "quality-alerts"
        
        print(f"✅ Alert producer initialized, topic: {self.topic}")

    def _delivery_report(self, err, msg):
        """Callback for message delivery reports"""
        if err is not None:
            print(f"❌ Alert delivery failed: {err}")
        else:
            print(f"✅ Alert delivered to {msg.topic()} [{msg.partition()}]")

    def produce_alert(
        self,
        product_id: str,
        analysis: Dict[str, Any],
        topic: str
    ) -> bool:
        """
        Produce a quality alert

        Args:
            product_id: Data product ID
            analysis: Analysis results from StreamAnalyzer
            topic: Source topic that triggered the alert

        Returns:
            True if alert was produced successfully
        """
        alert = {
            "alert_id": f"ALERT-{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}",
            "timestamp": datetime.utcnow().isoformat(),
            "product_id": product_id,
            "source_topic": topic,
            "severity": analysis.get("severity", "info"),
            "quality_score": analysis.get("quality_score", 0),
            "issues_found": analysis.get("issues_found", []),
            "recommendations": analysis.get("recommendations", []),
            "sample_size": analysis.get("sample_size", 0),
            "analysis_type": "stream_quality"
        }

        try:
            self.producer.produce(
                topic=self.topic,
                key=product_id.encode('utf-8'),
                value=json.dumps(alert).encode('utf-8'),
                callback=self._delivery_report
            )
            self.producer.poll(0)
            
            print(f"🚨 Alert produced: {alert['alert_id']} - {alert['severity']}")
            return True

        except Exception as e:
            print(f"❌ Failed to produce alert: {e}")
            return False

    def flush(self, timeout: float = 10.0) -> int:
        """Flush pending alerts"""
        return self.producer.flush(timeout)

    def close(self):
        """Close producer"""
        self.flush()
        print("👋 Alert producer closed")
