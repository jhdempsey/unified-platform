#!/usr/bin/env python3
"""
Create Kafka topics with Avro schema registration
Binds schemas from schemas/avro/*.avsc to topics in Confluent Kafka
"""

import json
import time
from pathlib import Path
from typing import Dict, List

from confluent_kafka.admin import AdminClient, NewTopic
from confluent_kafka.schema_registry import SchemaRegistryClient, Schema


# Configuration
KAFKA_BOOTSTRAP_SERVERS = "localhost:19093"
SCHEMA_REGISTRY_URL = "http://localhost:18081"

# Topic configurations
TOPICS = [
    {
        "name": "supplier-events",
        "schema_file": "supplier-event.avsc",
        "partitions": 3,
        "replication_factor": 1,
        "config": {
            "retention.ms": "604800000",  # 7 days
            "cleanup.policy": "delete"
        }
    },
    {
        "name": "order-events",
        "schema_file": "order-event.avsc",
        "partitions": 3,
        "replication_factor": 1,
        "config": {
            "retention.ms": "2592000000",  # 30 days
            "cleanup.policy": "delete"
        }
    },
    {
        "name": "product-events",
        "schema_file": "product-created.avsc",
        "partitions": 2,
        "replication_factor": 1,
        "config": {
            "retention.ms": "-1",  # Retain forever
            "cleanup.policy": "compact"
        }
    },
    {
        "name": "quality-alerts",
        "schema_file": "quality-alert.avsc",
        "partitions": 2,
        "replication_factor": 1,
        "config": {
            "retention.ms": "2592000000",  # 30 days
            "cleanup.policy": "delete"
        }
    },
    {
        "name": "lineage-events",
        "schema_file": "lineage-event.avsc",
        "partitions": 2,
        "replication_factor": 1,
        "config": {
            "retention.ms": "-1",  # Retain forever
            "cleanup.policy": "compact"
        }
    }
]


def load_avro_schema(schema_file: str) -> str:
    """Load Avro schema from file"""
    schema_path = Path(__file__).parent.parent / "schemas" / "avro" / schema_file
    
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(schema_path, 'r') as f:
        schema_dict = json.load(f)
    
    return json.dumps(schema_dict)


def create_topics(admin_client: AdminClient, topics_config: List[Dict]):
    """Create Kafka topics"""
    print("🔧 Creating Kafka topics...")
    
    # Get existing topics
    metadata = admin_client.list_topics(timeout=10)
    existing_topics = set(metadata.topics.keys())
    
    # Create new topics
    new_topics = []
    for topic_config in topics_config:
        topic_name = topic_config["name"]
        
        if topic_name in existing_topics:
            print(f"  ⏭️  Topic '{topic_name}' already exists")
            continue
        
        new_topic = NewTopic(
            topic=topic_name,
            num_partitions=topic_config["partitions"],
            replication_factor=topic_config["replication_factor"],
            config=topic_config.get("config", {})
        )
        new_topics.append(new_topic)
        print(f"  ➕ Creating topic '{topic_name}' "
              f"({topic_config['partitions']} partitions)")
    
    if new_topics:
        # Create topics
        futures = admin_client.create_topics(new_topics)
        
        # Wait for creation
        for topic_name, future in futures.items():
            try:
                future.result()  # Block until topic is created
                print(f"  ✅ Topic '{topic_name}' created successfully")
            except Exception as e:
                print(f"  ❌ Failed to create topic '{topic_name}': {e}")
    else:
        print("  ℹ️  No new topics to create")
    
    print()


def register_schemas(schema_registry_client: SchemaRegistryClient, 
                     topics_config: List[Dict]):
    """Register Avro schemas in Schema Registry"""
    print("📋 Registering Avro schemas...")
    
    for topic_config in topics_config:
        topic_name = topic_config["name"]
        schema_file = topic_config["schema_file"]
        
        try:
            # Load schema
            schema_str = load_avro_schema(schema_file)
            schema = Schema(schema_str, schema_type="AVRO")
            
            # Register schema for topic value
            subject = f"{topic_name}-value"
            schema_id = schema_registry_client.register_schema(
                subject_name=subject,
                schema=schema
            )
            
            print(f"  ✅ Registered schema for '{subject}' (ID: {schema_id})")
            
        except Exception as e:
            print(f"  ❌ Failed to register schema for '{topic_name}': {e}")
    
    print()


def verify_setup(admin_client: AdminClient, 
                 schema_registry_client: SchemaRegistryClient,
                 topics_config: List[Dict]):
    """Verify topics and schemas are properly set up"""
    print("🔍 Verifying setup...")
    
    # Verify topics
    metadata = admin_client.list_topics(timeout=10)
    
    for topic_config in topics_config:
        topic_name = topic_config["name"]
        
        if topic_name in metadata.topics:
            topic_metadata = metadata.topics[topic_name]
            print(f"  ✅ Topic '{topic_name}': "
                  f"{len(topic_metadata.partitions)} partitions")
        else:
            print(f"  ❌ Topic '{topic_name}': NOT FOUND")
    
    print()
    
    # Verify schemas
    for topic_config in topics_config:
        topic_name = topic_config["name"]
        subject = f"{topic_name}-value"
        
        try:
            schema = schema_registry_client.get_latest_version(subject)
            print(f"  ✅ Schema '{subject}': version {schema.version}")
        except Exception as e:
            print(f"  ❌ Schema '{subject}': {e}")
    
    print()


def main():
    """Main execution"""
    print("=" * 70)
    print("🚀 Kafka Topic & Schema Registry Setup")
    print("=" * 70)
    print()
    
    # Initialize clients
    print("🔌 Connecting to Kafka and Schema Registry...")
    
    admin_client = AdminClient({
        'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS
    })
    
    schema_registry_client = SchemaRegistryClient({
        'url': SCHEMA_REGISTRY_URL
    })
    
    print(f"  ✅ Kafka: {KAFKA_BOOTSTRAP_SERVERS}")
    print(f"  ✅ Schema Registry: {SCHEMA_REGISTRY_URL}")
    print()
    
    # Create topics
    create_topics(admin_client, TOPICS)
    
    # Wait a moment for topics to be ready
    time.sleep(2)
    
    # Register schemas
    register_schemas(schema_registry_client, TOPICS)
    
    # Verify everything
    verify_setup(admin_client, schema_registry_client, TOPICS)
    
    print("=" * 70)
    print("✅ Setup complete!")
    print("=" * 70)
    print()
    print("📝 Summary:")
    print(f"  • {len(TOPICS)} topics created/verified")
    print(f"  • {len(TOPICS)} schemas registered")
    print()
    print("🎯 Next steps:")
    print("  1. Test with: python scripts/test-kafka-avro.py")
    print("  2. View topics: kafka-topics --list --bootstrap-server localhost:19093")
    print("  3. View schemas: curl http://localhost:18081/subjects")
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n⚠️  Interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
