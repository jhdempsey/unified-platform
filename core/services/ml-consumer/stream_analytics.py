"""Stream Analytics - Real-time aggregations and windowing."""

import json
import sys
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict

from confluent_kafka import Consumer, KafkaError

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class StreamAnalytics:
    """Real-time stream processing with windowing."""

    def __init__(self, bootstrap_servers: str = "localhost:9092"):
        self.consumer_config = {
            "bootstrap.servers": bootstrap_servers,
            "group.id": "analytics-consumer-group",
            "auto.offset.reset": "earliest",
        }
        self.consumer = Consumer(self.consumer_config)

        # Windows: 1-minute, 5-minute, 1-hour
        self.window_1min = defaultdict(
            lambda: {
                "count": 0,
                "total_value": 0,
                "high_risk": 0,
                "start_time": datetime.now(),
            }
        )
        self.window_5min = defaultdict(
            lambda: {
                "count": 0,
                "total_value": 0,
                "high_risk": 0,
                "start_time": datetime.now(),
            }
        )

        # Running totals
        self.total_orders = 0
        self.total_revenue = 0
        self.total_high_risk = 0

        # Product analytics
        self.product_stats = defaultdict(
            lambda: {"count": 0, "revenue": 0, "avg_risk": 0}
        )

    def reset_window_if_expired(self, window: Dict, duration_minutes: int):
        """Reset window if time expired."""
        for key in list(window.keys()):
            elapsed = datetime.now() - window[key]["start_time"]
            if elapsed > timedelta(minutes=duration_minutes):
                del window[key]

    def process_order_event(self, order: Dict[str, Any]):
        """Process order for analytics."""
        order_value = order["quantity"] * order["unit_price"]
        product_name = order["product"]["name"]
        timestamp = datetime.now()

        # Update 1-minute window
        key_1min = timestamp.strftime("%Y-%m-%d %H:%M")
        self.window_1min[key_1min]["count"] += 1
        self.window_1min[key_1min]["total_value"] += order_value
        if order["priority"] == "high":
            self.window_1min[key_1min]["high_risk"] += 1

        # Update 5-minute window
        minute_bucket = (timestamp.minute // 5) * 5
        key_5min = timestamp.strftime(f"%Y-%m-%d %H:{minute_bucket:02d}")
        self.window_5min[key_5min]["count"] += 1
        self.window_5min[key_5min]["total_value"] += order_value
        if order["priority"] == "high":
            self.window_5min[key_5min]["high_risk"] += 1

        # Update running totals
        self.total_orders += 1
        self.total_revenue += order_value
        if order["priority"] == "high":
            self.total_high_risk += 1

        # Update product stats
        self.product_stats[product_name]["count"] += 1
        self.product_stats[product_name]["revenue"] += order_value

        # Clean old windows
        self.reset_window_if_expired(self.window_1min, 1)
        self.reset_window_if_expired(self.window_5min, 5)

    def print_analytics(self):
        """Print current analytics."""
        print("\n" + "=" * 80)
        print("📊 REAL-TIME ANALYTICS DASHBOARD")
        print("=" * 80)

        # Overall stats
        print("\n📈 Overall Statistics:")
        print(f"   Total Orders: {self.total_orders}")
        print(f"   Total Revenue: ${self.total_revenue:,.2f}")
        print(f"   High Risk Orders: {self.total_high_risk}")
        if self.total_orders > 0:
            risk_pct = (self.total_high_risk / self.total_orders) * 100
            avg_value = self.total_revenue / self.total_orders
            print(f"   Risk Rate: {risk_pct:.1f}%")
            print(f"   Avg Order Value: ${avg_value:.2f}")

        # 1-minute window
        if self.window_1min:
            print("\n⏱️  Last Minute:")
            for key, data in sorted(self.window_1min.items())[-3:]:
                print(
                    f"   {key}: {data['count']} orders, "
                    f"${data['total_value']:.2f}, "
                    f"{data['high_risk']} high-risk"
                )

        # 5-minute window
        if self.window_5min:
            print("\n⏱️  5-Minute Windows:")
            for key, data in sorted(self.window_5min.items())[-3:]:
                print(
                    f"   {key}: {data['count']} orders, "
                    f"${data['total_value']:.2f}, "
                    f"{data['high_risk']} high-risk"
                )

        # Top products
        if self.product_stats:
            print("\n🏆 Top Products by Revenue:")
            sorted_products = sorted(
                self.product_stats.items(), key=lambda x: x[1]["revenue"], reverse=True
            )[:5]
            for product, stats in sorted_products:
                print(
                    f"   {product}: {stats['count']} orders, "
                    f"${stats['revenue']:.2f}"
                )

        print("=" * 80 + "\n")

    def run(self):
        """Main analytics loop."""
        self.consumer.subscribe(["supply-chain.orders"])

        print("\n📊 Stream Analytics started")
        print("📥 Consuming: supply-chain.orders")
        print("🔄 Windows: 1-min, 5-min rolling aggregations")
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

                order = json.loads(msg.value().decode("utf-8"))
                self.process_order_event(order)

                message_count += 1

                # Print dashboard every 10 messages
                if message_count % 10 == 0:
                    self.print_analytics()

        except KeyboardInterrupt:
            print("\n\n⏹️  Analytics stopped")
            self.print_analytics()
        finally:
            self.consumer.close()


if __name__ == "__main__":
    analytics = StreamAnalytics()
    analytics.run()
