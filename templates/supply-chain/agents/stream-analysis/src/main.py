"""
Stream Analysis Agent
AI-powered real-time data quality monitoring
"""

import os
import sys
import signal
from typing import List, Dict, Any

from analyzer import StreamAnalyzer
from kafka_consumer import StreamConsumer
from alert_producer import AlertProducer


class StreamAnalysisAgent:
    """
    Main agent that coordinates:
    - Consuming from Kafka topics
    - Analyzing data quality with AI
    - Producing quality alerts
    """
    
    def __init__(self):
        """Initialize agent components"""
        print("🤖 Initializing Stream Analysis Agent...")
        
        # Initialize components
        self.analyzer = StreamAnalyzer()
        self.consumer = StreamConsumer(
            group_id="stream-analysis-agent",
            auto_offset_reset="latest"  # Only analyze new messages
        )
        self.alert_producer = AlertProducer()
        
        # Topics to monitor
        self.topics = [
            "supplier-events",
            "order-events",
            "product-events"
        ]
        
        # Stats
        self.stats = {
            "batches_analyzed": 0,
            "messages_analyzed": 0,
            "alerts_produced": 0
        }
        
        print("✅ Agent initialized")
    
    def on_batch_received(self, topic: str, messages: List[Dict[str, Any]]):
        """
        Callback when a batch of messages is received
        
        Args:
            topic: Source topic
            messages: List of deserialized messages
        """
        print(f"\n📊 Analyzing batch from {topic}: {len(messages)} messages")
        
        # Analyze batch
        analysis = self.analyzer.analyze_batch(messages, topic)
        
        # Update stats
        self.stats["batches_analyzed"] += 1
        self.stats["messages_analyzed"] += len(messages)
        
        # Print analysis
        print(f"   Quality Score: {analysis.get('quality_score', 'N/A')}")
        print(f"   Severity: {analysis.get('severity', 'N/A')}")
        print(f"   Issues: {len(analysis.get('issues_found', []))}")
        
        # Determine if alert needed
        if self.analyzer.should_alert(analysis):
            print(f"   🚨 Alert triggered!")
            
            # Produce alert
            product_id = f"PROD-{topic.upper()}"  # Simplified - in production, lookup actual product
            self.alert_producer.produce_alert(
                analysis=analysis,
                topic=topic,
                product_id=product_id
            )
            self.alert_producer.flush()
            
            self.stats["alerts_produced"] += 1
        else:
            print(f"   ✅ No alert needed")
    
    def start(self):
        """Start the agent"""
        print("\n" + "=" * 70)
        print("🚀 STREAM ANALYSIS AGENT STARTING")
        print("=" * 70)
        print(f"📥 Monitoring topics: {', '.join(self.topics)}")
        print(f"🤖 AI Analysis: {'Enabled' if self.analyzer.client else 'Disabled (rule-based)'}")
        print("=" * 70)
        print("\nPress Ctrl+C to stop\n")
        
        # Subscribe to topics
        self.consumer.subscribe(self.topics)
        
        # Start consuming
        try:
            self.consumer.start_consuming(
                on_batch=self.on_batch_received,
                batch_size=50,  # Analyze in batches of 50
                batch_interval=10.0  # Or after 10 seconds
            )
        except KeyboardInterrupt:
            print("\n⚠️  Agent interrupted by user")
        finally:
            self.shutdown()
    
    def shutdown(self):
        """Shutdown agent"""
        print("\n" + "=" * 70)
        print("👋 SHUTTING DOWN STREAM ANALYSIS AGENT")
        print("=" * 70)
        
        # Print stats
        print(f"\n📊 Final Statistics:")
        print(f"   Batches analyzed: {self.stats['batches_analyzed']}")
        print(f"   Messages analyzed: {self.stats['messages_analyzed']}")
        print(f"   Alerts produced: {self.stats['alerts_produced']}")
        
        # Close components
        self.consumer.stop()
        self.alert_producer.close()
        
        print("\n✅ Agent shutdown complete")


def main():
    """Main entry point"""
    # Create agent
    agent = StreamAnalysisAgent()
    
    # Handle signals
    def signal_handler(sig, frame):
        print("\n⚠️  Received shutdown signal")
        agent.shutdown()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start agent
    agent.start()


if __name__ == "__main__":
    main()
