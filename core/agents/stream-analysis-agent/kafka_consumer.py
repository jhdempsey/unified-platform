"""
Kafka Consumer for Stream Analysis
Consumes events and triggers analysis with SASL_SSL support
"""

import os
import json
import uuid
from typing import List, Callable, Optional
from confluent_kafka import Consumer, KafkaError, KafkaException
from confluent_kafka.serialization import SerializationContext, MessageField
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroDeserializer


class StreamConsumer:
    """
    Consumes messages from Kafka topics with Avro/JSON deserialization
    Supports SASL_SSL authentication for Confluent Cloud
    """

    def __init__(
        self,
        group_id: str = "stream-analyzer",
        bootstrap_servers: str = None,
        schema_registry_url: str = None,
        auto_offset_reset: str = "latest"
    ):
        """
        Initialize consumer

        Args:
            group_id: Consumer group ID
            bootstrap_servers: Kafka bootstrap servers
            schema_registry_url: Schema Registry URL
            auto_offset_reset: Where to start consuming (earliest/latest)
        """
        self.group_id = group_id
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

        # Base consumer config
        consumer_config = {
            'bootstrap.servers': self.bootstrap_servers,
            'group.id': group_id,
            'auto.offset.reset': auto_offset_reset,
            'enable.auto.commit': False,
        }

        # Add SASL config if using SASL_SSL (Confluent Cloud)
        if security_protocol == "SASL_SSL":
            consumer_config.update({
                'security.protocol': security_protocol,
                'sasl.mechanism': sasl_mechanism,
                'sasl.username': sasl_username,
                'sasl.password': sasl_password,
            })
            print(f"🔐 Consumer using SASL_SSL authentication to {self.bootstrap_servers}")
        else:
            print(f"🔓 Consumer using PLAINTEXT connection to {self.bootstrap_servers}")

        # Initialize consumer
        self.consumer = Consumer(consumer_config)
        print(f"✅ Consumer initialized with group: {group_id}")

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

        # Cache for deserializers
        self.deserializers = {}

        # Batch processing
        self.batch_size = 100
        self.batch_timeout_ms = 5000

    def subscribe(self, topics: List[str]):
        """Subscribe to topics"""
        self.consumer.subscribe(topics)
        print(f"📥 Subscribed to: {topics}")

    def _deserialize_message(self, msg) -> Optional[dict]:
        """
        Deserialize message, trying Avro first then JSON
        """
        try:
            value = msg.value()
            if value is None:
                return None

            # Try JSON first (simpler)
            try:
                return json.loads(value.decode('utf-8'))
            except (json.JSONDecodeError, UnicodeDecodeError):
                pass

            # Try Avro if Schema Registry available
            if self.schema_registry_client:
                try:
                    topic = msg.topic()
                    if topic not in self.deserializers:
                        # Get schema from registry
                        schema = self.schema_registry_client.get_latest_version(f"{topic}-value")
                        self.deserializers[topic] = AvroDeserializer(
                            self.schema_registry_client,
                            schema.schema.schema_str
                        )
                    
                    return self.deserializers[topic](
                        value,
                        SerializationContext(topic, MessageField.VALUE)
                    )
                except Exception as e:
                    print(f"⚠️ Avro deserialization failed: {e}")

            # Return raw bytes as fallback
            return {"_raw": value.hex(), "_length": len(value)}

        except Exception as e:
            print(f"❌ Deserialization error: {e}")
            return None

    def consume_batch(
        self,
        callback: Callable[[str, List[dict]], None],
        timeout_seconds: float = 5.0
    ) -> int:
        """
        Consume a batch of messages and call callback

        Args:
            callback: Function(topic, messages) to call with batch
            timeout_seconds: Max time to wait for batch

        Returns:
            Number of messages consumed
        """
        messages_by_topic = {}
        start_time = __import__('time').time()
        count = 0

        while count < self.batch_size:
            elapsed = __import__('time').time() - start_time
            if elapsed >= timeout_seconds:
                break

            remaining = timeout_seconds - elapsed
            msg = self.consumer.poll(timeout=min(1.0, remaining))

            if msg is None:
                continue

            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    continue
                else:
                    print(f"❌ Consumer error: {msg.error()}")
                    continue

            # Deserialize
            data = self._deserialize_message(msg)
            if data:
                topic = msg.topic()
                if topic not in messages_by_topic:
                    messages_by_topic[topic] = []
                messages_by_topic[topic].append(data)
                count += 1

        # Call callback for each topic batch
        for topic, messages in messages_by_topic.items():
            if messages:
                callback(topic, messages)

        # Commit offsets
        if count > 0:
            self.consumer.commit(asynchronous=False)

        return count

    def close(self):
        """Close consumer"""
        self.consumer.close()
        print("👋 Consumer closed")
