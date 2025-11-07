"""
Discovery Agent - Main Entry Point
Combines topic discovery, schema analysis, and catalog API
"""

import sys
from topic_discovery import TopicDiscoveryAgent
from schema_analyzer import SchemaSimilarityAnalyzer

def main():
    """Run complete discovery and analysis"""
    
    print("🔍 Starting Data Intelligence Discovery...")
    
    # Run discovery
    discovery_agent = TopicDiscoveryAgent(sample_size=50)
    topics = discovery_agent.discover_and_analyze_all()
    discovery_agent.close()
    
    # Run analysis
    analyzer = SchemaSimilarityAnalyzer()
    recommendations = analyzer.compare_topics(topics)
    
    # Get managed topics
    managed_topics = []  # TODO: Fetch from Product Service
    unmanaged = analyzer.detect_unmanaged_topics(topics, managed_topics)
    
    # Print summary
    print("\n" + "=" * 70)
    print("📊 DISCOVERY COMPLETE")
    print("=" * 70)
    print(f"Topics discovered: {len(topics)}")
    print(f"Consolidation opportunities: {len(recommendations)}")
    print(f"Unmanaged topics: {len(unmanaged)}")
    print("=" * 70)
    
    print("\n💡 To start the catalog API:")
    print("   python catalog_api.py")

if __name__ == "__main__":
    main()
