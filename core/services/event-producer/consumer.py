"""Order Event Consumer - Consumes and displays supply chain order events."""

import json

from confluent_kafka import Consumer, KafkaError


class OrderEventConsumer:
    """Consumes order events from Kafka."""

    def __init__(
        self,
        bootstrap_servers: str = "localhost:9092",
        group_id: str = "order-consumer-group",
    ):
        self.config = {
            "bootstrap.servers": bootstrap_servers,
            "group.id": group_id,
            "auto.offset.reset": "earliest",
            "enable.auto.commit": True,
        }
        self.consumer = Consumer(self.config)
        self.topic = "supply-chain.orders"

    def consume_events(self, max_messages: int = 100):
        """Consume events from Kafka."""
        self.consumer.subscribe([self.topic])

        print(f"\n👂 Listening for events on topic: {self.topic}")
        print(f"📊 Will consume up to {max_messages} messages\n")
        print("=" * 80)

        try:
            message_count = 0
            while message_count < max_messages:
                msg = self.consumer.poll(timeout=1.0)

                if msg is None:
                    continue

                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        print(f"\n✅ Reached end of partition {msg.partition()}")
                    else:
                        print(f"❌ Error: {msg.error()}")
                    continue

                event = json.loads(msg.value().decode("utf-8"))
                message_count += 1

                print(f"\n📦 Event #{message_count}")
                print(f"   Order ID: {event['order_id']}")
                product = event["product"]
                print(f"   Product: {product['name']} ({product['category']})")
                supplier = event["supplier"]
                reliability = supplier["reliability"] * 100
                print(f"   Supplier: {supplier['name']} ")
                print(f"             (Reliability: {reliability:.0f}%)")
                price = event["unit_price"]
                print(f"   Quantity: {event['quantity']} units @ ${price}/unit")
                priority = event["priority"]
                print(f"   Delivery: {event['delivery_days']} days ")
                print(f"             ({priority} priority)")
                distance = event["distance_miles"]
                weather = event["weather_risk"]
                print(f"   Distance: {distance} miles | Weather Risk: {weather}")
                perishable = event["product"]["perishable"]
                print(f"   Perishable: {'Yes ⚠️' if perishable else 'No'}")
                print("-" * 80)

        except KeyboardInterrupt:
            print("\n\n⏹️  Consumer stopped by user")
        finally:
            self.consumer.close()
            print(f"\n✅ Consumed {message_count} messages total")


if __name__ == "__main__":
    consumer = OrderEventConsumer()
    consumer.consume_events(max_messages=100)
