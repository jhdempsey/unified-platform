"""
Topic Discovery Agent
Continuously scans Kafka to discover all topics, infer schemas, and track usage
"""

import os
import json
from typing import Dict, Any, List, Optional, Set
from datetime import datetime
from collections import defaultdict

from confluent_kafka import Consumer, TopicPartition, KafkaException
from confluent_kafka.admin import AdminClient


class TopicDiscoveryAgent:
    """
    Discovers all Kafka topics and analyzes them:
    - Lists all topics in cluster
    - Samples messages to infer schemas
    - Detects producers/consumers
    - Identifies usage patterns
    - Flags unmanaged/ungoverned topics
    """
    
    def __init__(
        self,
        bootstrap_servers: str = None,
        sample_size: int = 100
    ):
        """
        Initialize discovery agent
        
        Args:
            bootstrap_servers: Kafka bootstrap servers
            sample_size: Number of messages to sample per topic
        """
        self.bootstrap_servers = bootstrap_servers or os.getenv(
            "KAFKA_BOOTSTRAP_SERVERS",
            "localhost:19093"
        )
        self.sample_size = sample_size
        
        # Get SASL credentials from environment (for Confluent Cloud)
        security_protocol = os.getenv("KAFKA_SECURITY_PROTOCOL", "PLAINTEXT")
        sasl_mechanism = os.getenv("KAFKA_SASL_MECHANISM", "")
        sasl_username = os.getenv("KAFKA_SASL_USERNAME", "")
        sasl_password = os.getenv("KAFKA_SASL_PASSWORD", "")
        
        # Base config
        base_config = {
            'bootstrap.servers': self.bootstrap_servers
        }
        
        # Add SASL config if using SASL_SSL (Confluent Cloud)
        if security_protocol == "SASL_SSL":
            base_config.update({
                'security.protocol': security_protocol,
                'sasl.mechanism': sasl_mechanism,
                'sasl.username': sasl_username,
                'sasl.password': sasl_password,
            })
            print(f"🔐 Using SASL_SSL authentication to {self.bootstrap_servers}")
        else:
            print(f"🔓 Using PLAINTEXT connection to {self.bootstrap_servers}")
        
        # Initialize admin client
        self.admin_client = AdminClient(base_config)
        
        # Consumer config (includes consumer-specific settings)
        consumer_config = {
            **base_config,
            'group.id': 'topic-discovery-agent',
            'auto.offset.reset': 'earliest',
            'enable.auto.commit': False
        }
        
        # Consumer for sampling
        self.consumer = Consumer(consumer_config)
    
    def discover_all_topics(self) -> List[Dict[str, Any]]:
        """
        Discover all topics in Kafka cluster
        
        Returns:
            List of topic information dictionaries
        """
        print("🔍 Discovering all Kafka topics...")
        
        # Get cluster metadata
        metadata = self.admin_client.list_topics(timeout=10)
        
        topics_info = []
        
        for topic_name, topic_metadata in metadata.topics.items():
            # Skip internal topics
            if topic_name.startswith('_') or topic_name.startswith('__'):
                continue
            
            print(f"   Found: {topic_name}")
            
            topic_info = {
                "topic_name": topic_name,
                "partitions": len(topic_metadata.partitions),
                "discovered_at": datetime.utcnow().isoformat(),
                "is_internal": False
            }
            
            topics_info.append(topic_info)
        
        print(f"✅ Discovered {len(topics_info)} topics")
        return topics_info
    
    def sample_topic(self, topic_name: str) -> Dict[str, Any]:
        """
        Sample messages from a topic to infer schema and patterns
        
        Args:
            topic_name: Topic to sample
            
        Returns:
            Analysis results including inferred schema
        """
        print(f"\n📊 Sampling topic: {topic_name}")
        
        result = {
            "topic_name": topic_name,
            "sampled_at": datetime.utcnow().isoformat(),
            "sample_size": 0,
            "messages": [],
            "inferred_schema": None,
            "has_schema_registry": False,
            "data_types": {},
            "field_coverage": {},
            "patterns": {}
        }
        
        try:
            # Subscribe to topic
            self.consumer.subscribe([topic_name])
            
            messages_collected = 0
            timeout_count = 0
            max_timeouts = 3
            
            # Collect sample messages
            while messages_collected < self.sample_size and timeout_count < max_timeouts:
                msg = self.consumer.poll(timeout=2.0)
                
                if msg is None:
                    timeout_count += 1
                    continue
                
                if msg.error():
                    print(f"   ⚠️  Error: {msg.error()}")
                    continue
                
                # Try to parse message
                try:
                    # Try JSON first
                    value = json.loads(msg.value().decode('utf-8'))
                    result["messages"].append(value)
                    messages_collected += 1
                    
                except (json.JSONDecodeError, UnicodeDecodeError):
                    # Not JSON, could be Avro or binary
                    result["messages"].append({
                        "_raw_length": len(msg.value()),
                        "_format": "binary_or_avro"
                    })
                    messages_collected += 1
            
            result["sample_size"] = messages_collected
            
            # Unsubscribe
            self.consumer.unsubscribe()
            
            # Analyze collected messages
            if messages_collected > 0:
                result["inferred_schema"] = self._infer_schema(result["messages"])
                result["data_types"] = self._analyze_data_types(result["messages"])
                result["field_coverage"] = self._calculate_field_coverage(result["messages"])
                result["patterns"] = self._detect_patterns(result["messages"])
            
            print(f"   ✅ Sampled {messages_collected} messages")
            
        except Exception as e:
            print(f"   ❌ Sampling failed: {e}")
            result["error"] = str(e)
        
        return result
    
    def _infer_schema(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Infer schema from sample messages"""
        if not messages:
            return {}
        
        # Collect all fields seen
        all_fields = set()
        field_types = defaultdict(set)
        
        for msg in messages:
            if isinstance(msg, dict) and "_format" not in msg:
                for field, value in msg.items():
                    all_fields.add(field)
                    field_types[field].add(type(value).__name__)
        
        # Build inferred schema
        schema = {
            "type": "record",
            "name": "InferredSchema",
            "fields": []
        }
        
        for field in sorted(all_fields):
            types = field_types[field]
            
            # Determine Avro type
            if len(types) == 1:
                python_type = list(types)[0]
                avro_type = self._python_to_avro_type(python_type)
            else:
                # Union type
                avro_type = ["null"] + [self._python_to_avro_type(t) for t in types]
            
            schema["fields"].append({
                "name": field,
                "type": avro_type,
                "inferred": True
            })
        
        return schema
    
    def _python_to_avro_type(self, python_type: str) -> str:
        """Map Python type to Avro type"""
        mapping = {
            "str": "string",
            "int": "long",
            "float": "double",
            "bool": "boolean",
            "list": {"type": "array", "items": "string"},
            "dict": {"type": "map", "values": "string"}
        }
        return mapping.get(python_type, "string")
    
    def _analyze_data_types(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze data types in messages"""
        type_counts = defaultdict(lambda: defaultdict(int))
        
        for msg in messages:
            if isinstance(msg, dict) and "_format" not in msg:
                for field, value in msg.items():
                    type_counts[field][type(value).__name__] += 1
        
        return dict(type_counts)
    
    def _calculate_field_coverage(self, messages: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate what % of messages have each field"""
        if not messages:
            return {}
        
        field_counts = defaultdict(int)
        total_messages = len([m for m in messages if isinstance(m, dict) and "_format" not in m])
        
        if total_messages == 0:
            return {}
        
        for msg in messages:
            if isinstance(msg, dict) and "_format" not in msg:
                for field in msg.keys():
                    field_counts[field] += 1
        
        return {
            field: (count / total_messages) * 100
            for field, count in field_counts.items()
        }
    
    def _detect_patterns(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Detect patterns in the data"""
        patterns = {
            "has_timestamp": False,
            "has_id_field": False,
            "has_nested_objects": False,
            "average_field_count": 0,
            "potential_keys": []
        }
        
        if not messages:
            return patterns
        
        valid_messages = [m for m in messages if isinstance(m, dict) and "_format" not in m]
        if not valid_messages:
            return patterns
        
        # Check for common patterns
        first_msg = valid_messages[0]
        
        # Timestamp fields
        timestamp_fields = ['timestamp', 'created_at', 'updated_at', 'event_time', 'ts']
        patterns["has_timestamp"] = any(field in first_msg for field in timestamp_fields)
        
        # ID fields
        id_fields = ['id', 'event_id', 'order_id', 'customer_id', 'supplier_id']
        patterns["has_id_field"] = any(field in first_msg for field in id_fields)
        patterns["potential_keys"] = [field for field in id_fields if field in first_msg]
        
        # Nested objects
        patterns["has_nested_objects"] = any(
            isinstance(value, (dict, list))
            for msg in valid_messages
            for value in msg.values()
        )
        
        # Average field count
        patterns["average_field_count"] = sum(
            len(msg) for msg in valid_messages
        ) / len(valid_messages)
        
        return patterns
    
    def discover_and_analyze_all(self) -> List[Dict[str, Any]]:
        """
        Complete discovery: find all topics and analyze them
        
        Returns:
            List of analyzed topics
        """
        print("=" * 70)
        print("🔍 TOPIC DISCOVERY & ANALYSIS")
        print("=" * 70)
        
        # Step 1: Discover topics
        print("\n📍 STEP 1: Discovering Kafka topics...")
        topics = self.discover_all_topics()
        
        # Step 2: Analyze each topic
        print("\n📍 STEP 2: Analyzing topics...")
        analyzed_topics = []
        
        for topic_info in topics:
            topic_name = topic_info["topic_name"]
            
            # Sample and analyze
            analysis = self.sample_topic(topic_name)
            
            # Merge with topic info
            complete_info = {**topic_info, **analysis}
            analyzed_topics.append(complete_info)
        
        print("\n" + "=" * 70)
        print(f"✅ Discovery complete: {len(analyzed_topics)} topics analyzed")
        print("=" * 70)
        
        return analyzed_topics
    
    def close(self):
        """Close connections"""
        self.consumer.close()


if __name__ == "__main__":
    # Test discovery
    agent = TopicDiscoveryAgent(sample_size=50)
    
    try:
        topics = agent.discover_and_analyze_all()
        
        # Save results
        output_file = "discovered_topics.json"
        with open(output_file, "w") as f:
            json.dump(topics, f, indent=2, default=str)
        
        print(f"\n💾 Results saved to {output_file}")
        
        # Print summary
        print("\n📊 Summary:")
        for topic in topics:
            print(f"\n  Topic: {topic['topic_name']}")
            print(f"    Partitions: {topic['partitions']}")
            print(f"    Sample Size: {topic.get('sample_size', 0)}")
            if topic.get('inferred_schema'):
                field_count = len(topic['inferred_schema'].get('fields', []))
                print(f"    Fields: {field_count}")
            if topic.get('patterns'):
                print(f"    Has Timestamp: {topic['patterns'].get('has_timestamp')}")
                print(f"    Has ID Field: {topic['patterns'].get('has_id_field')}")
        
    finally:
        agent.close()
