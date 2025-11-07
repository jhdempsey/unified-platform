"""
Product Recommender Agent
Uses Claude AI to analyze discovered topics and recommend data products

This agent:
1. Analyzes discovered Kafka topics
2. Identifies patterns, relationships, and redundancies
3. Proposes data products that would add business value
4. Generates Flink SQL for materializing the products
"""

import os
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
import anthropic

from shared.config import config


class ProductRecommendation:
    """A recommended data product"""
    
    def __init__(
        self,
        product_name: str,
        confidence: float,
        reasoning: str,
        source_topics: List[str],
        proposed_output_topic: str,
        proposed_schema: Dict[str, Any],
        flink_sql: str,
        business_value: str,
        estimated_consumers: int = 0,
        priority: str = "MEDIUM"
    ):
        self.recommendation_id = self._generate_id()
        self.product_name = product_name
        self.confidence = confidence
        self.reasoning = reasoning
        self.source_topics = source_topics
        self.proposed_output_topic = proposed_output_topic
        self.proposed_schema = proposed_schema
        self.flink_sql = flink_sql
        self.business_value = business_value
        self.estimated_consumers = estimated_consumers
        self.priority = priority
        self.created_at = datetime.utcnow().isoformat()
        self.status = "PENDING_REVIEW"
    
    def _generate_id(self) -> str:
        """Generate unique recommendation ID"""
        import uuid
        return f"REC-{uuid.uuid4().hex[:8].upper()}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "recommendation_id": self.recommendation_id,
            "product_name": self.product_name,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "source_topics": self.source_topics,
            "proposed_output_topic": self.proposed_output_topic,
            "proposed_schema": self.proposed_schema,
            "flink_sql": self.flink_sql,
            "business_value": self.business_value,
            "estimated_consumers": self.estimated_consumers,
            "priority": self.priority,
            "created_at": self.created_at,
            "status": self.status
        }


class ProductRecommenderAgent:
    """
    AI-powered agent that recommends data products based on discovered topics
    """
    
    def __init__(self, api_key: str = None):
        """Initialize the recommender agent"""
        self.api_key = api_key or config.ANTHROPIC_API_KEY
        
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not configured")
        
        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.model = "claude-sonnet-4-20250514"
        
        print("🤖 Product Recommender Agent initialized")
    
    def analyze_and_recommend(
        self,
        discovered_topics: List[Dict[str, Any]],
        max_recommendations: int = 10
    ) -> List[ProductRecommendation]:
        """
        Analyze discovered topics and generate product recommendations
        
        Args:
            discovered_topics: List of topics from TopicDiscoveryAgent
            max_recommendations: Maximum number of recommendations to generate
            
        Returns:
            List of ProductRecommendation objects
        """
        print(f"🔍 Analyzing {len(discovered_topics)} discovered topics...")
        
        # Prepare topic data for analysis
        topic_summary = self._prepare_topic_summary(discovered_topics)
        
        # Use Claude to analyze and generate recommendations
        print("🤖 Asking Claude AI for recommendations...")
        recommendations_data = self._get_ai_recommendations(
            topic_summary,
            max_recommendations
        )
        
        # Convert to ProductRecommendation objects
        recommendations = []
        for rec_data in recommendations_data:
            try:
                rec = ProductRecommendation(
                    product_name=rec_data["product_name"],
                    confidence=rec_data["confidence"],
                    reasoning=rec_data["reasoning"],
                    source_topics=rec_data["source_topics"],
                    proposed_output_topic=rec_data["proposed_output_topic"],
                    proposed_schema=rec_data["proposed_schema"],
                    flink_sql=rec_data["flink_sql"],
                    business_value=rec_data["business_value"],
                    estimated_consumers=rec_data.get("estimated_consumers", 0),
                    priority=rec_data.get("priority", "MEDIUM")
                )
                recommendations.append(rec)
            except Exception as e:
                print(f"⚠️  Failed to create recommendation: {e}")
                continue
        
        print(f"✅ Generated {len(recommendations)} recommendations")
        return recommendations
    
    def _prepare_topic_summary(
        self,
        discovered_topics: List[Dict[str, Any]]
    ) -> str:
        """
        Prepare a summary of discovered topics for AI analysis
        """
        summary_parts = []
        
        for i, topic in enumerate(discovered_topics, 1):
            topic_info = f"""
Topic {i}: {topic.get('topic_name', 'UNKNOWN')}
  Partitions: {topic.get('partitions', 0)}
  Messages Sampled: {topic.get('messages_sampled', 0)}
  Quality Score: {topic.get('quality_score', 0)}/100
  Has Schema Registry: {topic.get('has_schema_registry', False)}
  
  Inferred Schema:
{json.dumps(topic.get('inferred_schema', {}), indent=4)}
  
  Sample Patterns:
{json.dumps(topic.get('patterns', {}), indent=4)}
  
  Field Coverage:
{json.dumps(topic.get('field_coverage', {}), indent=4)}
"""
            summary_parts.append(topic_info)
        
        return "\n".join(summary_parts)
    
    def _get_ai_recommendations(
        self,
        topic_summary: str,
        max_recommendations: int
    ) -> List[Dict[str, Any]]:
        """
        Use Claude AI to analyze topics and generate recommendations
        """
        
        prompt = f"""You are a data platform architect analyzing Kafka topics to recommend high-value data products.

DISCOVERED TOPICS:
{topic_summary}

TASK:
Analyze these topics and recommend up to {max_recommendations} data products that would provide significant business value. For each recommendation:

1. Identify topics that should be combined/transformed into a unified data product
2. Look for:
   - Topics with related entities (same IDs, similar schemas)
   - Topics that could be joined to create richer datasets
   - Topics with redundant data that should be consolidated
   - Topics that need aggregation or enrichment

3. For each recommended product, provide:
   - A clear, business-friendly product name
   - Confidence score (0.0-1.0) based on how strong the recommendation is
   - Reasoning explaining WHY this product would be valuable
   - List of source topics to combine
   - Proposed output topic name (use kebab-case)
   - A complete Avro schema for the product
   - Flink SQL that transforms the source topics into the product
   - Business value statement
   - Priority (HIGH/MEDIUM/LOW)
   - Estimated number of potential consumers

FLINK SQL GUIDELINES:
- Use proper Flink SQL syntax with CREATE TABLE and INSERT INTO
- Include proper joins on related fields
- Add aggregations where appropriate (windowing, grouping)
- Use meaningful column aliases
- Include timestamp handling with WATERMARK for event-time processing

OUTPUT FORMAT:
Return a JSON array of recommendations. Each recommendation must have this exact structure:

{{
  "product_name": "Human-readable product name",
  "confidence": 0.85,
  "reasoning": "Detailed explanation of why this product is valuable...",
  "source_topics": ["topic1", "topic2"],
  "proposed_output_topic": "kebab-case-topic-name",
  "proposed_schema": {{
    "type": "record",
    "name": "ProductName",
    "namespace": "com.platform.products.domain",
    "fields": [
      {{"name": "field1", "type": "string"}},
      {{"name": "field2", "type": "long"}}
    ]
  }},
  "flink_sql": "CREATE TABLE product_table (...) WITH (...); INSERT INTO product_table SELECT ... FROM ...;",
  "business_value": "Clear statement of business value",
  "priority": "HIGH",
  "estimated_consumers": 5
}}

Focus on recommendations that:
- Consolidate redundant data
- Join related entities
- Add business value through transformation
- Would be used by multiple teams/consumers

Return ONLY the JSON array, no additional text."""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=16000,
                temperature=0.7,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            # Extract the response
            response_text = response.content[0].text
            
            # Parse JSON
            # Handle potential markdown code blocks
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()
            
            recommendations = json.loads(response_text)
            
            print(f"✅ Claude generated {len(recommendations)} recommendations")
            return recommendations
            
        except json.JSONDecodeError as e:
            print(f"❌ Failed to parse AI response: {e}")
            print(f"Response was: {response_text[:500]}...")
            return []
        except Exception as e:
            print(f"❌ AI recommendation failed: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def refine_recommendation(
        self,
        recommendation: ProductRecommendation,
        user_feedback: str
    ) -> ProductRecommendation:
        """
        Refine a recommendation based on user feedback
        
        Args:
            recommendation: Original recommendation
            user_feedback: User's feedback/changes
            
        Returns:
            Updated recommendation
        """
        print(f"🔄 Refining recommendation: {recommendation.product_name}")
        
        prompt = f"""You are helping refine a data product recommendation based on user feedback.

ORIGINAL RECOMMENDATION:
{json.dumps(recommendation.to_dict(), indent=2)}

USER FEEDBACK:
{user_feedback}

TASK:
Update the recommendation based on the user's feedback. Maintain the same JSON structure but incorporate their changes/suggestions.

Return ONLY the updated JSON object, no additional text."""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=8000,
                temperature=0.5,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            response_text = response.content[0].text
            
            # Parse JSON
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()
            
            updated_data = json.loads(response_text)
            
            # Create updated recommendation
            updated = ProductRecommendation(
                product_name=updated_data["product_name"],
                confidence=updated_data["confidence"],
                reasoning=updated_data["reasoning"],
                source_topics=updated_data["source_topics"],
                proposed_output_topic=updated_data["proposed_output_topic"],
                proposed_schema=updated_data["proposed_schema"],
                flink_sql=updated_data["flink_sql"],
                business_value=updated_data["business_value"],
                estimated_consumers=updated_data.get("estimated_consumers", 0),
                priority=updated_data.get("priority", "MEDIUM")
            )
            
            print(f"✅ Recommendation refined")
            return updated
            
        except Exception as e:
            print(f"❌ Refinement failed: {e}")
            return recommendation


if __name__ == "__main__":
    # Test the recommender
    print("🧪 Testing Product Recommender Agent\n")
    
    # Sample discovered topics
    sample_topics = [
        {
            "topic_name": "supplier-events",
            "partitions": 3,
            "messages_sampled": 100,
            "quality_score": 75,
            "has_schema_registry": True,
            "inferred_schema": {
                "type": "record",
                "fields": [
                    {"name": "supplier_id", "type": "string"},
                    {"name": "supplier_name", "type": "string"},
                    {"name": "status", "type": "string"}
                ]
            }
        },
        {
            "topic_name": "order-events",
            "partitions": 5,
            "messages_sampled": 200,
            "quality_score": 80,
            "has_schema_registry": True,
            "inferred_schema": {
                "type": "record",
                "fields": [
                    {"name": "order_id", "type": "string"},
                    {"name": "supplier_id", "type": "string"},
                    {"name": "amount", "type": "double"}
                ]
            }
        }
    ]
    
    try:
        agent = ProductRecommenderAgent()
        recommendations = agent.analyze_and_recommend(sample_topics, max_recommendations=3)
        
        print(f"\n📊 Generated {len(recommendations)} recommendations:\n")
        for rec in recommendations:
            print(f"🎯 {rec.product_name}")
            print(f"   Confidence: {rec.confidence * 100:.0f}%")
            print(f"   Priority: {rec.priority}")
            print(f"   Sources: {', '.join(rec.source_topics)}")
            print(f"   Output: {rec.proposed_output_topic}")
            print(f"   Reasoning: {rec.reasoning[:100]}...")
            print()
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
