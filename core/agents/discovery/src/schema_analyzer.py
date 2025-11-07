"""
Schema Similarity Analyzer
Uses AI to compare schemas, detect redundancy, and suggest consolidation
"""

import os
import json
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

try:
    from anthropic import Anthropic
except ImportError:
    Anthropic = None


class SchemaSimilarityAnalyzer:
    """
    AI-powered analysis of schema overlap and redundancy
    - Compares schemas across topics
    - Detects field overlap
    - Identifies redundant topics
    - Suggests consolidation strategies
    - Generates unified schemas
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize analyzer"""
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        
        if self.api_key and Anthropic:
            self.client = Anthropic(api_key=self.api_key)
            self.ai_enabled = True
        else:
            self.client = None
            self.ai_enabled = False
            print("⚠️  AI disabled: ANTHROPIC_API_KEY not set")
    
    def compare_topics(
        self,
        topics: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Compare all topics to find overlaps and redundancy
        
        Args:
            topics: List of discovered topics with inferred schemas
            
        Returns:
            List of recommendations for consolidation
        """
        print("\n🔍 Analyzing schema similarity across topics...")
        
        recommendations = []
        
        # Compare each pair of topics
        for i, topic1 in enumerate(topics):
            for topic2 in topics[i+1:]:
                similarity = self._calculate_similarity(topic1, topic2)
                
                if similarity["overlap_percentage"] > 50:  # >50% overlap
                    print(f"   ⚠️  High overlap: {topic1['topic_name']} ↔ {topic2['topic_name']} ({similarity['overlap_percentage']:.1f}%)")
                    
                    recommendation = {
                        "type": "CONSOLIDATION",
                        "severity": "HIGH" if similarity["overlap_percentage"] > 80 else "MEDIUM",
                        "topics": [topic1['topic_name'], topic2['topic_name']],
                        "similarity": similarity,
                        "suggested_action": "Consider consolidating these topics into a single data product"
                    }
                    
                    # Use AI to generate detailed recommendation
                    if self.ai_enabled:
                        ai_recommendation = self._generate_ai_recommendation(
                            topic1, topic2, similarity
                        )
                        recommendation["ai_analysis"] = ai_recommendation
                    
                    recommendations.append(recommendation)
        
        print(f"✅ Found {len(recommendations)} consolidation opportunities")
        
        return recommendations
    
    def _calculate_similarity(
        self,
        topic1: Dict[str, Any],
        topic2: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate similarity between two topics"""
        schema1 = topic1.get("inferred_schema") or {}
        schema2 = topic2.get("inferred_schema") or {}
        
        fields1 = set(f["name"] for f in schema1.get("fields", []))
        fields2 = set(f["name"] for f in schema2.get("fields", []))
        
        if not fields1 or not fields2:
            return {
                "overlap_percentage": 0,
                "common_fields": [],
                "unique_to_topic1": [],
                "unique_to_topic2": []
            }
        
        common = fields1 & fields2
        unique1 = fields1 - fields2
        unique2 = fields2 - fields1
        
        # Calculate overlap as percentage of smaller schema
        overlap_pct = (len(common) / min(len(fields1), len(fields2))) * 100
        
        return {
            "overlap_percentage": overlap_pct,
            "common_fields": sorted(list(common)),
            "unique_to_topic1": sorted(list(unique1)),
            "unique_to_topic2": sorted(list(unique2)),
            "field_count": {
                "topic1": len(fields1),
                "topic2": len(fields2),
                "common": len(common)
            }
        }
    
    def _generate_ai_recommendation(
        self,
        topic1: Dict[str, Any],
        topic2: Dict[str, Any],
        similarity: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Use AI to generate detailed consolidation recommendation"""
        
        prompt = f"""You are a data platform architect analyzing schema overlap between Kafka topics.

Topic 1: {topic1['topic_name']}
Schema: {json.dumps(topic1.get('inferred_schema', {}), indent=2)}
Patterns: {json.dumps(topic1.get('patterns', {}), indent=2)}

Topic 2: {topic2['topic_name']}
Schema: {json.dumps(topic2.get('inferred_schema', {}), indent=2)}
Patterns: {json.dumps(topic2.get('patterns', {}), indent=2)}

Similarity Analysis:
- Overlap: {similarity['overlap_percentage']:.1f}%
- Common fields: {', '.join(similarity['common_fields'])}
- Unique to topic1: {', '.join(similarity['unique_to_topic1'])}
- Unique to topic2: {', '.join(similarity['unique_to_topic2'])}

Please analyze:
1. Are these topics truly redundant or serving different purposes?
2. What would be the impact of consolidating them?
3. What would a unified schema look like?
4. What migration strategy would you recommend?
5. Any risks or concerns?

Respond in JSON format:
{{
  "is_redundant": true/false,
  "confidence": "LOW|MEDIUM|HIGH",
  "consolidation_feasible": true/false,
  "unified_schema": {{ avro schema }},
  "migration_strategy": ["step 1", "step 2", ...],
  "risks": ["risk 1", "risk 2", ...],
  "benefits": ["benefit 1", "benefit 2", ...],
  "recommendation": "detailed recommendation"
}}"""
        
        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=2048,
                temperature=0.3,
                messages=[{"role": "user", "content": prompt}]
            )
            
            result_text = response.content[0].text
            
            # Extract JSON
            if "```json" in result_text:
                json_start = result_text.find("```json") + 7
                json_end = result_text.find("```", json_start)
                result_text = result_text[json_start:json_end].strip()
            
            return json.loads(result_text)
            
        except Exception as e:
            print(f"   ⚠️  AI analysis failed: {e}")
            return {
                "error": str(e),
                "recommendation": "Manual review recommended"
            }
    
    def detect_unmanaged_topics(
        self,
        discovered_topics: List[Dict[str, Any]],
        managed_topics: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Identify topics that are not managed by the platform
        
        Args:
            discovered_topics: All discovered topics
            managed_topics: List of topic names that are managed
            
        Returns:
            List of unmanaged topics with recommendations
        """
        print("\n🔍 Detecting unmanaged topics...")
        
        unmanaged = []
        
        for topic in discovered_topics:
            topic_name = topic["topic_name"]
            
            if topic_name not in managed_topics:
                # This topic is unmanaged (wild west!)
                quality_score = self._assess_quality(topic)
                
                recommendation = {
                    "topic_name": topic_name,
                    "status": "UNMANAGED",
                    "quality_score": quality_score,
                    "issues": self._identify_issues(topic),
                    "suggested_action": self._suggest_action(topic, quality_score)
                }
                
                # Use AI for detailed recommendation if enabled
                if self.ai_enabled and quality_score < 70:
                    recommendation["ai_recommendation"] = self._generate_governance_recommendation(topic)
                
                unmanaged.append(recommendation)
                
                status = "⚠️" if quality_score < 70 else "ℹ️"
                print(f"   {status}  {topic_name} (Quality: {quality_score:.1f})")
        
        print(f"✅ Found {len(unmanaged)} unmanaged topics")
        
        return unmanaged
    
    def _assess_quality(self, topic: Dict[str, Any]) -> float:
        """Assess data quality of a topic"""
        score = 100.0
        
        # Deduct for missing schema
        if not topic.get("has_schema_registry"):
            score -= 30
        
        # Deduct for low field coverage
        field_coverage = topic.get("field_coverage", {})
        if field_coverage:
            avg_coverage = sum(field_coverage.values()) / len(field_coverage)
            if avg_coverage < 90:
                score -= (90 - avg_coverage) / 2
        
        # Deduct for no timestamp
        patterns = topic.get("patterns", {})
        if not patterns.get("has_timestamp"):
            score -= 10
        
        # Deduct for no ID field
        if not patterns.get("has_id_field"):
            score -= 10
        
        return max(0, score)
    
    def _identify_issues(self, topic: Dict[str, Any]) -> List[str]:
        """Identify specific issues with a topic"""
        issues = []
        
        if not topic.get("has_schema_registry"):
            issues.append("No schema registered in Schema Registry")
        
        patterns = topic.get("patterns", {})
        if not patterns.get("has_timestamp"):
            issues.append("Missing timestamp field")
        
        if not patterns.get("has_id_field"):
            issues.append("Missing unique identifier field")
        
        field_coverage = topic.get("field_coverage", {})
        incomplete_fields = [
            field for field, coverage in field_coverage.items()
            if coverage < 95
        ]
        if incomplete_fields:
            issues.append(f"Incomplete fields: {', '.join(incomplete_fields)}")
        
        return issues
    
    def _suggest_action(self, topic: Dict[str, Any], quality_score: float) -> str:
        """Suggest action based on quality score"""
        if quality_score < 50:
            return "CRITICAL: Register schema and fix data quality issues immediately"
        elif quality_score < 70:
            return "WARNING: Promote to managed data product with proper governance"
        else:
            return "INFO: Consider promoting to managed data product"
    
    def _generate_governance_recommendation(self, topic: Dict[str, Any]) -> Dict[str, Any]:
        """Generate AI recommendation for governing an unmanaged topic"""
        
        prompt = f"""You are a data governance expert. Analyze this unmanaged Kafka topic:

Topic: {topic['topic_name']}
Inferred Schema: {json.dumps(topic.get('inferred_schema', {}), indent=2)}
Patterns: {json.dumps(topic.get('patterns', {}), indent=2)}
Issues: {json.dumps(topic.get('issues', []), indent=2)}

Recommend how to govern this topic:
1. What schema should be registered?
2. What quality rules should be enforced?
3. How to migrate existing consumers?
4. Priority level for governance?

Respond in JSON:
{{
  "priority": "LOW|MEDIUM|HIGH|CRITICAL",
  "recommended_schema": {{ avro schema }},
  "quality_rules": [{{ rule objects }}],
  "migration_steps": ["step 1", "step 2", ...],
  "estimated_effort": "description",
  "business_impact": "description"
}}"""
        
        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=2048,
                temperature=0.3,
                messages=[{"role": "user", "content": prompt}]
            )
            
            result_text = response.content[0].text
            
            if "```json" in result_text:
                json_start = result_text.find("```json") + 7
                json_end = result_text.find("```", json_start)
                result_text = result_text[json_start:json_end].strip()
            
            return json.loads(result_text)
            
        except Exception as e:
            return {"error": str(e)}


if __name__ == "__main__":
    # Test with discovered topics
    import sys
    
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    else:
        input_file = "../discovery-agent/discovered_topics.json"
    
    try:
        with open(input_file, 'r') as f:
            topics = json.load(f)
        
        analyzer = SchemaSimilarityAnalyzer()
        
        # Compare topics for redundancy
        recommendations = analyzer.compare_topics(topics)
        
        # Detect unmanaged topics
        managed_topics = []  # Would come from Product Service
        unmanaged = analyzer.detect_unmanaged_topics(topics, managed_topics)
        
        # Save results
        results = {
            "analyzed_at": datetime.utcnow().isoformat(),
            "consolidation_recommendations": recommendations,
            "unmanaged_topics": unmanaged
        }
        
        output_file = "schema_analysis.json"
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\n💾 Analysis saved to {output_file}")
        
        # Print summary
        print("\n📊 Summary:")
        print(f"   Consolidation opportunities: {len(recommendations)}")
        print(f"   Unmanaged topics: {len(unmanaged)}")
        
        if recommendations:
            print("\n   Top recommendations:")
            for rec in recommendations[:3]:
                print(f"     • {' ↔ '.join(rec['topics'])} ({rec['similarity']['overlap_percentage']:.1f}% overlap)")
        
    except FileNotFoundError:
        print(f"❌ File not found: {input_file}")
        print("   Run topic_discovery.py first to generate discovered_topics.json")
