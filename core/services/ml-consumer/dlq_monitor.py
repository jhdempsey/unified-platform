"""Dead Letter Queue Monitor - View and replay failed messages."""

import json

from confluent_kafka import Consumer, KafkaError


class DLQMonitor:
    """Monitor dead letter queue for failed events."""

    def __init__(self, bootstrap_servers: str = "localhost:9092"):
        self.config = {
            "bootstrap.servers": bootstrap_servers,
            "group.id": "dlq-monitor-group",
            "auto.offset.reset": "earliest",
        }
        self.consumer = Consumer(self.config)
        self.dlq_topic = "supply-chain.dead-letter"

    def run(self):
        """Monitor DLQ for failed messages."""
        self.consumer.subscribe([self.dlq_topic])

        print("\n☠️  Dead Letter Queue Monitor")
        print(f"📥 Monitoring: {self.dlq_topic}")
        print("=" * 80)

        message_count = 0

        try:
            while True:
                msg = self.consumer.poll(timeout=1.0)

                if msg is None:
                    continue

                if msg.error():
                    if msg.error().code() != KafkaError._PARTITION_EOF:
                        print(f"❌ Error: {msg.error()}")
                    continue

                dlq_event = json.loads(msg.value().decode("utf-8"))
                message_count += 1

                print(f"\n{'='*80}")
                print(f"☠️  DLQ Message #{message_count}")
                print(f"{'='*80}")
                print(f"Timestamp: {dlq_event['timestamp']}")
                print(f"Error: {dlq_event['error']}")
                print(f"Retry Count: {dlq_event['retry_count']}")
                print(f"Reason: {dlq_event['dlq_reason']}")
                print("\nOriginal Message Preview:")
                original = dlq_event["original_message"]
                if isinstance(original, str):
                    original = json.loads(original)
                print(f"  Order ID: {original.get('order_id', 'N/A')}")
                print(f"  Tenant: {original.get('tenant_id', 'N/A')}")
                print(f"{'='*80}\n")

        except KeyboardInterrupt:
            print("\n\n⏹️  DLQ Monitor stopped")
            print(f"Total DLQ messages seen: {message_count}")
        finally:
            self.consumer.close()


if __name__ == "__main__":
    monitor = DLQMonitor()
    monitor.run()
