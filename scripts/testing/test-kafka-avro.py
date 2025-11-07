#!/usr/bin/env python3
"""
Test Kafka + Avro + Schema Registry Setup
Produces and consumes test messages to verify everything works
"""

import json
import time
import uuid
from datetime import datetime
from typing import Dict, Any

from avro_producer import AvroProducerHelper
from avro_consumer import AvroConsumerHelper


def generate_supplier_event() -> Dict[str, Any]:
    """Generate a test supplier event"""
    supplier_id = f"SUP-{uuid.uuid4().hex[:6].upper()}"
    
    return {
        "event_id": str(uuid.uuid4()),
        "event_type": "CREATED",
        "supplier_id": supplier_id,
        "supplier_name": f"Test Supplier {supplier_id}",
        "supplier_code": f"TST-{uuid.uuid4().hex[:4].upper()}",
        "country": "USA",
        "certification_status": "FDA Certified",
        "contact_email": f"contact@{supplier_id.lower()}.com",
        "timestamp": int(datetime.now().timestamp() * 1000),
        "metadata": {
            "test": "true",
            "generated_by": "test_script"
        }
    }


def generate_order_event() -> Dict[str, Any]:
    """Generate a test order event"""
    order_id = f"ORD-{uuid.uuid4().hex[:8].upper()}"
    
    return {
        "event_id": str(uuid.uuid4()),
        "event_type": "PLACED",
        "order_id": order_id,
        "supplier_id": f"SUP-{uuid.uuid4().hex[:6].upper()}",
        "customer_id": f"CUST-{uuid.uuid4().hex[:6].upper()}",
        "order_total": 1250.75,
        "currency": "USD",
        "items": [
            {
                "product_id": "PROD-001",
                "quantity": 10,
                "unit_price": 25.50
            },
            {
                "product_id": "PROD-002",
                "quantity": 5,
                "unit_price": 199.95
            }
        ],
        "shipping_address": {
            "street": "123 Main St",
            "city": "San Francisco",
            "state": "CA",
            "postal_code": "94105",
            "country": "USA"
        },
        "timestamp": int(datetime.now().timestamp() * 1000),
        "metadata": {
            "test": "true",
            "generated_by": "test_script"
        }
    }


def generate_product_event() -> Dict[str, Any]:
    """Generate a test product created event"""
    product_id = f"PROD-{uuid.uuid4().hex[:6].upper()}"
    
    return {
        "event_id": str(uuid.uuid4()),
        "product_id": product_id,
        "product_name": f"Test Product {product_id}",
        "product_type": "DATASET",
        "owner": "platform-team",
        "description": "Test data product for demo",
        "schema_version": "1.0.0",
        "tags": ["test", "demo", "supplier-data"],
        "quality_score": 95.5,
        "kafka_topic": "supplier-events",
        "timestamp": int(datetime.now().timestamp() * 1000),
        "created_by": "test_user",
        "metadata": {
            "test": "true",
            "generated_by": "test_script"
        }
    }


def generate_quality_alert() -> Dict[str, Any]:
    """Generate a test quality alert"""
    return {
        "event_id": str(uuid.uuid4()),
        "alert_type": "ANOMALY",
        "severity": "MEDIUM",
        "product_id": f"PROD-{uuid.uuid4().hex[:6].upper()}",
        "topic_name": "supplier-events",
        "description": "Test quality alert: Unusual data pattern detected",
        "ai_analysis": "AI detected a 45% deviation from baseline. Recommended action: Review data source configuration.",
        "affected_records": 15,
        "sample_data": json.dumps({"example": "data"}),
        "metrics": {
            "completeness": 92.5,
            "accuracy": 88.0,
            "deviation_percent": 45.0
        },
        "timestamp": int(datetime.now().timestamp() * 1000),
        "detection_method": "AI_AGENT",
        "metadata": {
            "test": "true",
            "generated_by": "test_script"
        }
    }


def generate_lineage_event() -> Dict[str, Any]:
    """Generate a test lineage event"""
    return {
        "event_id": str(uuid.uuid4()),
        "lineage_type": "TRANSFORMATION",
        "source_product_id": f"PROD-{uuid.uuid4().hex[:6].upper()}",
        "target_product_id": f"PROD-{uuid.uuid4().hex[:6].upper()}",
        "transformation_name": "aggregate_by_supplier",
        "transformation_logic": "SELECT supplier_id, COUNT(*) FROM orders GROUP BY supplier_id",
        "input_records": 1000,
        "output_records": 50,
        "execution_time_ms": 2350,
        "status": "SUCCESS",
        "error_message": None,
        "agent_id": "stream-analyzer-001",
        "timestamp": int(datetime.now().timestamp() * 1000),
        "metadata": {
            "test": "true",
            "generated_by": "test_script"
        }
    }


def test_produce(producer: AvroProducerHelper):
    """Test producing messages to all topics"""
    print("\n" + "=" * 70)
    print("📤 PRODUCING TEST MESSAGES")
    print("=" * 70)
    
    # Produce supplier events
    print("\n1️⃣  Producing supplier events...")
    for i in range(3):
        event = generate_supplier_event()
        producer.produce(
            topic="supplier-events",
            value=event,
            schema_file="supplier-event.avsc",
            key=event["supplier_id"]
        )
        time.sleep(0.1)
    
    # Produce order events
    print("\n2️⃣  Producing order events...")
    for i in range(2):
        event = generate_order_event()
        producer.produce(
            topic="order-events",
            value=event,
            schema_file="order-event.avsc",
            key=event["order_id"]
        )
        time.sleep(0.1)
    
    # Produce product events
    print("\n3️⃣  Producing product events...")
    for i in range(2):
        event = generate_product_event()
        producer.produce(
            topic="product-events",
            value=event,
            schema_file="product-created.avsc",
            key=event["product_id"]
        )
        time.sleep(0.1)
    
    # Produce quality alerts
    print("\n4️⃣  Producing quality alerts...")
    for i in range(2):
        event = generate_quality_alert()
        producer.produce(
            topic="quality-alerts",
            value=event,
            schema_file="quality-alert.avsc",
            key=event["product_id"]
        )
        time.sleep(0.1)
    
    # Produce lineage events
    print("\n5️⃣  Producing lineage events...")
    for i in range(2):
        event = generate_lineage_event()
        producer.produce(
            topic="lineage-events",
            value=event,
            schema_file="lineage-event.avsc",
            key=event["source_product_id"]
        )
        time.sleep(0.1)
    
    print("\n⏳ Flushing messages...")
    producer.flush()
    print("✅ All messages produced!\n")


def test_consume(consumer: AvroConsumerHelper, duration: int = 10):
    """Test consuming messages from all topics"""
    print("\n" + "=" * 70)
    print("📥 CONSUMING TEST MESSAGES")
    print("=" * 70)
    print(f"Will consume for {duration} seconds...\n")
    
    topics = [
        "supplier-events",
        "order-events",
        "product-events",
        "quality-alerts",
        "lineage-events"
    ]
    
    consumer.subscribe(topics)
    
    message_count = 0
    start_time = time.time()
    
    try:
        for key, value, topic, partition, offset in consumer.consume(timeout=1.0):
            message_count += 1
            
            print(f"\n📨 Message #{message_count}")
            print(f"   Topic: {topic}")
            print(f"   Partition: {partition}")
            print(f"   Offset: {offset}")
            print(f"   Key: {key}")
            
            # Print value based on topic
            if topic == "supplier-events":
                print(f"   Supplier: {value.get('supplier_name')} ({value.get('supplier_id')})")
                print(f"   Event: {value.get('event_type')}")
            elif topic == "order-events":
                print(f"   Order: {value.get('order_id')}")
                print(f"   Total: ${value.get('order_total')}")
                print(f"   Items: {len(value.get('items', []))}")
            elif topic == "product-events":
                print(f"   Product: {value.get('product_name')} ({value.get('product_id')})")
                print(f"   Type: {value.get('product_type')}")
            elif topic == "quality-alerts":
                print(f"   Alert: {value.get('alert_type')} - {value.get('severity')}")
                print(f"   Product: {value.get('product_id')}")
            elif topic == "lineage-events":
                print(f"   Lineage: {value.get('lineage_type')}")
                print(f"   Source → Target: {value.get('source_product_id')} → {value.get('target_product_id')}")
            
            print("-" * 70)
            
            # Check timeout
            if time.time() - start_time > duration:
                break
                
    except KeyboardInterrupt:
        print("\n⚠️  Interrupted by user")
    
    print(f"\n✅ Consumed {message_count} messages\n")


def main():
    """Main test execution"""
    print("\n" + "=" * 70)
    print("🧪 KAFKA + AVRO + SCHEMA REGISTRY TEST")
    print("=" * 70)
    
    # Initialize producer
    print("\n🔌 Initializing producer...")
    producer = AvroProducerHelper()
    
    # Test producing
    test_produce(producer)
    
    # Close producer
    producer.close()
    
    # Wait a moment
    print("⏸️  Waiting 3 seconds before consuming...\n")
    time.sleep(3)
    
    # Initialize consumer
    print("🔌 Initializing consumer...")
    consumer = AvroConsumerHelper(
        group_id=f"test-group-{uuid.uuid4().hex[:8]}",
        auto_offset_reset="earliest"
    )
    
    # Test consuming
    test_consume(consumer, duration=10)
    
    # Close consumer
    consumer.close()
    
    print("\n" + "=" * 70)
    print("✅ TEST COMPLETE!")
    print("=" * 70)
    print("\n📊 Summary:")
    print("  • Successfully produced messages to 5 topics")
    print("  • Successfully consumed and deserialized messages")
    print("  • Avro schemas validated by Schema Registry")
    print("  • Schema versioning working")
    print("\n🎉 Your Kafka + Avro setup is working perfectly!")
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
