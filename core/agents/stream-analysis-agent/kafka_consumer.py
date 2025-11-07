"""
Kafka Consumer for Stream Analysis
Consumes events and triggers analysis
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
        
        # Initialize Schema Registry client
        try:
            self.schema_registry_client = SchemaRegistryClient({
                'url': self.schema_registry_url
            })
            self.deserializer = AvroDeserializer(self.schema_registry_client)
            print(f"✅ Schema Registry connected: {self.schema_registry_url}")
        except Exception as e:
            print(f"⚠️  Schema Registry unavailable: {e}")
            self.schema_registry_client = None
            self.deserializer = None
        
        # Initialize Kafka consumer
        self.consumer = Consumer({
            'bootstrap.servers': self.bootstrap_servers,
            'group.id': group_id,
            'auto.offset.reset': auto_offset_reset,
            'enable.auto.commit': True,
            'client.id': f'stream-analyzer-{uuid.uuid4().hex[:8]}',
            'max.poll.interval.ms': 600000,  # 10 min - allows time for AI analysis
            'session.timeout.ms': 60000,     # 1 min - detect true failures faster
            'heartbeat.interval.ms': 3000    # 3 sec - keep connection alive
        })
        
        self.running = False
    
    def subscribe(self, topics: List[str]):
        """Subscribe to topics"""
        self.consumer.subscribe(topics)
        print(f"📥 Subscribed to topics: {', '.join(topics)}")
    
    def consume_batch(
        self,
        batch_size: int = 100,
        timeout: float = 5.0
    ) -> List[tuple]:
        """
        Consume a batch of messages
        
        Args:
            batch_size: Maximum messages to consume
            timeout: Timeout for each poll (seconds)
            
        Returns:
            List of (topic, key, value, timestamp) tuples
        """
        messages = []
        
        for _ in range(batch_size):
            msg = self.consumer.poll(timeout=timeout)
            
            if msg is None:
                # No more messages
                break
            
            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    continue
                else:
                    print(f"❌ Consumer error: {msg.error()}")
                    continue
            
            try:
                # Try Avro deserialization first (if available)
                if self.deserializer:
                    try:
                        value = self.deserializer(
                            msg.value(),
                            SerializationContext(msg.topic(), MessageField.VALUE)
                        )
                    except Exception:
                        # Fallback to JSON
                        value = json.loads(msg.value().decode('utf-8'))
                else:
                    # No Avro deserializer, use JSON
                    value = json.loads(msg.value().decode('utf-8'))
                
                # Get key
                key = msg.key().decode('utf-8') if msg.key() else None
                
                messages.append((
                    msg.topic(),
                    key,
                    value,
                    msg.timestamp()[1] if msg.timestamp()[0] else None
                ))
                
            except Exception as e:
                print(f"⚠️  Failed to deserialize message: {e}")
                continue
        
        return messages
    
    def start_consuming(
        self,
        on_batch: Callable[[str, List[dict]], None],
        batch_size: int = 100,
        batch_interval: float = 5.0
    ):
        """
        Start consuming messages and call handler on batches
        
        Args:
            on_batch: Callback function(topic, messages)
            batch_size: Messages per batch
            batch_interval: Seconds to wait for batch
        """
        self.running = True
        print(f"🎧 Starting consumer (batch_size={batch_size}, interval={batch_interval}s)...")
        
        try:
            # Group messages by topic
            topic_batches = {}
            
            while self.running:
                # Consume batch
                messages = self.consume_batch(batch_size, batch_interval)
                
                if not messages:
                    # Process any pending batches
                    for topic, batch in topic_batches.items():
                        if batch:
                            on_batch(topic, batch)
                    topic_batches.clear()
                    continue
                
                # Group by topic
                for topic, key, value, timestamp in messages:
                    if topic not in topic_batches:
                        topic_batches[topic] = []
                    topic_batches[topic].append(value)
                
                # Process full batches
                for topic, batch in list(topic_batches.items()):
                    if len(batch) >= batch_size:
                        on_batch(topic, batch)
                        topic_batches[topic] = []
                
        except KeyboardInterrupt:
            print("\n⚠️  Consumer interrupted by user")
        except Exception as e:
            print(f"❌ Consumer error: {e}")
            raise
        finally:
            self.stop()
    
    def stop(self):
        """Stop consuming"""
        self.running = False
        if hasattr(self, 'consumer'):
            self.consumer.close()
            print("👋 Consumer closed")
