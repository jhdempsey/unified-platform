"""
AI Schema Generator
Uses Claude to generate Avro schemas from natural language descriptions
"""

import os
import json
from typing import Dict, Any, Optional, List
from datetime import datetime

try:
    from anthropic import Anthropic
except ImportError:
    Anthropic = None


class SchemaGenerator:
    """
    Generates data product schemas using AI
    Takes natural language requirements and creates:
    - Avro schema
    - Kafka topic configuration
    - Quality rules
    - Sample queries
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize schema generator"""
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        
        if not self.api_key or Anthropic is None:
            raise ValueError(
                "ANTHROPIC_API_KEY required for Product Generator Agent. "
                "This agent requires AI to function."
            )
        
        self.client = Anthropic(api_key=self.api_key)
    
    def generate_product(
        self,
        description: str,
        product_name: str,
        owner: str,
        additional_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate a complete data product from description
        
        Args:
            description: Natural language description of what user needs
            product_name: Proposed name for the product
            owner: Team or user who will own this product
            additional_context: Optional additional requirements
            
        Returns:
            Complete product specification with schema, config, etc.
        """
        print(f"🤖 Generating data product: {product_name}")
        print(f"   Description: {description}")
        
        # Build prompt
        prompt = self._build_generation_prompt(
            description,
            product_name,
            owner,
            additional_context
        )
        
        # Call Claude
        response = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            temperature=0.3,  # Lower temperature for more consistent schemas
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )
        
        # Parse response
        result_text = response.content[0].text
        
        # Extract JSON
        if "```json" in result_text:
            json_start = result_text.find("```json") + 7
            json_end = result_text.find("```", json_start)
            result_text = result_text[json_start:json_end].strip()
        
        result = json.loads(result_text)
        
        # Add metadata
        result["generated_at"] = datetime.utcnow().isoformat()
        result["generated_by"] = "AI_AGENT"
        result["product_name"] = product_name
        result["owner"] = owner
        
        print(f"✅ Product generated successfully")
        
        return result
    
    def _build_generation_prompt(
        self,
        description: str,
        product_name: str,
        owner: str,
        additional_context: Optional[Dict[str, Any]]
    ) -> str:
        """Build the AI prompt for product generation"""
        
        context_str = ""
        if additional_context:
            context_str = f"\n\nAdditional Context:\n{json.dumps(additional_context, indent=2)}"
        
        prompt = f"""You are an expert data architect for an intelligent data platform. A user needs a new data product.

User Request:
- Product Name: {product_name}
- Owner: {owner}
- Description: {description}{context_str}

Generate a complete data product specification including:

1. **Avro Schema**: Design an appropriate Avro schema for this data
2. **Product Type**: Determine if this should be DATASET, STREAM, API, REPORT, or ML_MODEL
3. **Kafka Configuration**: Recommend topic name, partitions, retention
4. **Data Sources**: Suggest where this data should come from
5. **Transformations**: Any data transformations needed
6. **Quality Rules**: Data quality checks and validation rules
7. **Tags**: Relevant searchable tags
8. **Sample Queries**: Example queries users might run

Return your response as JSON in this EXACT format:

{{
  "product_type": "DATASET|STREAM|API|REPORT|ML_MODEL",
  "description_enhanced": "Enhanced description with technical details",
  "avro_schema": {{
    "type": "record",
    "name": "ProductName",
    "namespace": "com.platform.products",
    "doc": "Description",
    "fields": [
      {{"name": "field1", "type": "string", "doc": "Field description"}},
      {{"name": "field2", "type": "long", "logicalType": "timestamp-millis"}},
      {{"name": "field3", "type": ["null", "double"], "default": null}}
    ]
  }},
  "kafka_config": {{
    "topic_name": "suggested-topic-name",
    "partitions": 3,
    "replication_factor": 2,
    "retention_ms": 604800000,
    "cleanup_policy": "delete"
  }},
  "data_sources": [
    {{"name": "source1", "type": "database", "description": "..."}}
  ],
  "transformations": [
    {{"step": 1, "description": "...", "logic": "SQL or description"}}
  ],
  "quality_rules": [
    {{
      "rule": "completeness",
      "field": "field_name",
      "threshold": 95.0,
      "description": "Field must be present in 95% of records"
    }}
  ],
  "tags": ["tag1", "tag2", "tag3"],
  "sample_queries": [
    {{"description": "Query description", "query": "SELECT ... FROM ..."}}
  ],
  "estimated_volume": {{
    "records_per_day": 10000,
    "size_per_record_bytes": 500
  }},
  "access_patterns": [
    "How users will access this data"
  ],
  "sla": {{
    "freshness_minutes": 60,
    "availability_percent": 99.9
  }}
}}

Important:
- Make the Avro schema production-ready with proper types and documentation
- Use logical types for timestamps, decimals, etc.
- Include sensible defaults for optional fields
- Ensure quality rules are specific and measurable
- Topic name should be kebab-case
- Be specific about data sources and transformations"""
        
        return prompt
    
    def validate_generated_schema(self, schema: Dict[str, Any]) -> tuple[bool, List[str]]:
        """
        Validate the generated Avro schema
        
        Returns:
            (is_valid, list_of_errors)
        """
        errors = []
        
        # Check required schema fields
        required_fields = ["type", "name", "namespace", "fields"]
        for field in required_fields:
            if field not in schema:
                errors.append(f"Missing required field: {field}")
        
        # Check schema type
        if schema.get("type") != "record":
            errors.append("Schema type must be 'record'")
        
        # Check fields
        if "fields" in schema:
            if not isinstance(schema["fields"], list):
                errors.append("Schema fields must be a list")
            elif len(schema["fields"]) == 0:
                errors.append("Schema must have at least one field")
            else:
                # Validate each field
                for i, field in enumerate(schema["fields"]):
                    if not isinstance(field, dict):
                        errors.append(f"Field {i} must be a dict")
                        continue
                    
                    if "name" not in field:
                        errors.append(f"Field {i} missing 'name'")
                    if "type" not in field:
                        errors.append(f"Field {i} missing 'type'")
        
        return len(errors) == 0, errors
    
    def refine_product(
        self,
        product_spec: Dict[str, Any],
        feedback: str
    ) -> Dict[str, Any]:
        """
        Refine a generated product based on user feedback
        
        Args:
            product_spec: Previously generated product specification
            feedback: User feedback/changes requested
            
        Returns:
            Refined product specification
        """
        print(f"🔄 Refining product based on feedback...")
        
        prompt = f"""You previously generated this data product specification:

{json.dumps(product_spec, indent=2)}

The user has provided feedback:
{feedback}

Please update the specification to incorporate this feedback. Return the complete updated JSON in the same format as before.

Important:
- Keep all fields that weren't mentioned in the feedback
- Only change what the user specifically requested
- Maintain consistency across all fields
- Ensure the Avro schema remains valid"""
        
        response = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            temperature=0.3,
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )
        
        # Parse response
        result_text = response.content[0].text
        
        if "```json" in result_text:
            json_start = result_text.find("```json") + 7
            json_end = result_text.find("```", json_start)
            result_text = result_text[json_start:json_end].strip()
        
        result = json.loads(result_text)
        result["refined_at"] = datetime.utcnow().isoformat()
        
        print(f"✅ Product refined successfully")
        
        return result


if __name__ == "__main__":
    # Test the generator
    generator = SchemaGenerator()
    
    product = generator.generate_product(
        description="I need a data product that tracks supplier performance metrics including on-time delivery rate, quality scores, and compliance status. This should update daily.",
        product_name="Supplier Performance Metrics",
        owner="procurement-team",
        additional_context={
            "industry": "food_supply_chain",
            "update_frequency": "daily",
            "consumers": ["procurement", "quality-assurance", "finance"]
        }
    )
    
    print("\n" + "=" * 70)
    print("Generated Product:")
    print("=" * 70)
    print(json.dumps(product, indent=2))
