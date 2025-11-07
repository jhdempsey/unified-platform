"""Alert Consumer - Displays high-risk order alerts."""

import json

from confluent_kafka import Consumer, KafkaError


class AlertConsumer:
    """Consumes and displays alerts."""

    def __init__(self, bootstrap_servers: str = "localhost:9092"):
        self.config = {
            "bootstrap.servers": bootstrap_servers,
            "group.id": "alert-consumer-group",
            "auto.offset.reset": "earliest",
        }
        self.consumer = Consumer(self.config)
        self.topic = "supply-chain.alerts"

    def run(self):
        """Consume and display alerts."""
        self.consumer.subscribe([self.topic])

        print("\n🚨 Alert Monitor Started")
        print(f"📥 Listening on: {self.topic}")
        print("=" * 80)
        print()

        try:
            while True:
                msg = self.consumer.poll(timeout=1.0)

                if msg is None:
                    continue

                if msg.error():
                    if msg.error().code() != KafkaError._PARTITION_EOF:
                        print(f"❌ Error: {msg.error()}")
                    continue

                alert = json.loads(msg.value().decode("utf-8"))

                print(f"\n{'='*80}")
                print(f"🚨 {alert['alert_type'].upper().replace('_', ' ')}")
                print(f"{'='*80}")
                print(f"Alert ID: {alert['alert_id']}")
                print(f"Order ID: {alert['order_id']}")
                print(f"Severity: {alert['severity'].upper()}")
                print(f"Time: {alert['timestamp']}")
                print("\n📋 Message:")
                print(f"   {alert['message']}")
                print("\n📊 Risk Details:")
                print(f"   Risk Score: {alert['details']['risk_score']:.1%}")
                on_time = alert["details"]["on_time_probability"]
                print(f"   On-Time Probability: {on_time:.1%}")
                print(f"   Product: {alert['details']['product']}")
                print(f"   Supplier: {alert['details']['supplier']}")
                days = alert["details"]["delivery_days"]
                print(f"   Delivery Window: {days} days")
                perishable = alert["details"]["perishable"]
                print(f"   Perishable: {'Yes ⚠️' if perishable else 'No'}")
                print("\n💡 Recommended Actions:")
                for action in alert["recommended_actions"]:
                    print(f"   • {action}")
                print(f"{'='*80}\n")

        except KeyboardInterrupt:
            print("\n\n⏹️  Alert monitor stopped")
        finally:
            self.consumer.close()


if __name__ == "__main__":
    consumer = AlertConsumer()
    consumer.run()
