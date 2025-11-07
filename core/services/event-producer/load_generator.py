"""Load Generator - Generate high-volume events for testing."""

import time

from producer import OrderEventProducer


class LoadGenerator:
    """Generate high-volume events to test throughput."""

    def __init__(self):
        self.producer = OrderEventProducer()

    def generate_load(self, events_per_second: int = 100, duration_seconds: int = 60):
        """
        Generate load at specified rate.

        Args:
            events_per_second: Target events per second
            duration_seconds: How long to run the test
        """
        delay_ms = 1000 / events_per_second
        total_events = events_per_second * duration_seconds

        print("\n🔥 Load Test Starting")
        print(f"   Target: {events_per_second} events/sec")
        print(f"   Duration: {duration_seconds} seconds")
        print(f"   Total Events: {total_events}")
        print("=" * 80)

        start_time = time.time()
        events_sent = 0

        try:
            for i in range(1, total_events + 1):
                event = self.producer.generate_order_event(i)
                self.producer.produce_event(event)
                events_sent += 1

                # Sleep to maintain target rate
                time.sleep(delay_ms / 1000.0)

                # Print progress every 100 events
                if i % 100 == 0:
                    elapsed = time.time() - start_time
                    actual_rate = events_sent / elapsed
                    print(
                        f"📊 Sent: {events_sent}/{total_events} | "
                        f"Rate: {actual_rate:.1f} events/sec | "
                        f"Elapsed: {elapsed:.1f}s"
                    )

            # Final flush
            self.producer.producer.flush()

            elapsed = time.time() - start_time
            actual_rate = events_sent / elapsed

            print("\n" + "=" * 80)
            print("✅ Load Test Complete")
            print(f"   Events Sent: {events_sent}")
            print(f"   Duration: {elapsed:.2f} seconds")
            print(f"   Actual Rate: {actual_rate:.1f} events/sec")
            print(f"   Target Rate: {events_per_second} events/sec")
            print(f"   Efficiency: {(actual_rate/events_per_second)*100:.1f}%")
            print("=" * 80)

        except KeyboardInterrupt:
            elapsed = time.time() - start_time
            actual_rate = events_sent / elapsed if elapsed > 0 else 0
            print(f"\n\n⏹️  Stopped after {events_sent} events")
            print(f"   Rate: {actual_rate:.1f} events/sec")


if __name__ == "__main__":
    import sys

    generator = LoadGenerator()

    # Default: 50 events/sec for 30 seconds
    events_per_sec = int(sys.argv[1]) if len(sys.argv) > 1 else 50
    duration = int(sys.argv[2]) if len(sys.argv) > 2 else 30

    generator.generate_load(events_per_second=events_per_sec, duration_seconds=duration)
