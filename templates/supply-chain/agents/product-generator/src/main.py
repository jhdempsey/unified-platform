"""
Product Generator Agent
AI-powered data product creation from natural language
"""

import os
import sys
import json
from typing import Dict, Any, Optional

from schema_generator import SchemaGenerator
from provisioner import ProductProvisioner


class ProductGeneratorAgent:
    """
    Main agent that coordinates:
    - Understanding user requirements
    - Generating schemas with AI
    - Provisioning infrastructure
    - Creating product records
    """
    
    def __init__(self):
        """Initialize agent"""
        print("🤖 Initializing Product Generator Agent...")
        
        # Check for API key
        if not os.getenv("ANTHROPIC_API_KEY"):
            print("❌ Error: ANTHROPIC_API_KEY environment variable required")
            print("   This agent needs Claude API to generate schemas")
            sys.exit(1)
        
        # Initialize components
        self.schema_generator = SchemaGenerator()
        self.provisioner = ProductProvisioner()
        
        print("✅ Agent initialized")
        print()
    
    def create_product_from_request(
        self,
        description: str,
        product_name: str,
        owner: str,
        additional_context: Optional[Dict[str, Any]] = None,
        auto_provision: bool = True
    ) -> Dict[str, Any]:
        """
        Create a complete data product from a natural language request
        
        Args:
            description: What the user wants
            product_name: Proposed name
            owner: Who will own this product
            additional_context: Optional extra requirements
            auto_provision: Whether to automatically provision infrastructure
            
        Returns:
            Complete result with product spec and provisioning status
        """
        print("=" * 70)
        print("🚀 CREATING DATA PRODUCT")
        print("=" * 70)
        print(f"Name: {product_name}")
        print(f"Owner: {owner}")
        print(f"Request: {description}")
        print("=" * 70)
        print()
        
        result = {
            "product_name": product_name,
            "owner": owner,
            "request": description,
            "success": False
        }
        
        try:
            # Step 1: Generate product specification with AI
            print("🧠 Step 1: Generating product specification with AI...")
            product_spec = self.schema_generator.generate_product(
                description=description,
                product_name=product_name,
                owner=owner,
                additional_context=additional_context
            )
            
            # Validate schema
            is_valid, errors = self.schema_generator.validate_generated_schema(
                product_spec["avro_schema"]
            )
            
            if not is_valid:
                result["error"] = f"Generated schema is invalid: {errors}"
                print(f"❌ Schema validation failed: {errors}")
                return result
            
            result["product_spec"] = product_spec
            print("✅ Product specification generated")
            print()
            
            # Step 2: Provision infrastructure (if auto_provision)
            if auto_provision:
                print("🔧 Step 2: Provisioning infrastructure...")
                provisioning_result = self.provisioner.provision_product(product_spec)
                result["provisioning"] = provisioning_result
                
                if not provisioning_result["success"]:
                    result["error"] = "Provisioning failed"
                    return result
            else:
                print("⏭️  Step 2: Skipping provisioning (auto_provision=False)")
                result["provisioning"] = {"status": "skipped"}
            
            result["success"] = True
            
            print()
            print("=" * 70)
            print("🎉 DATA PRODUCT CREATED SUCCESSFULLY!")
            print("=" * 70)
            
            # Print summary
            self._print_summary(result)
            
        except Exception as e:
            result["error"] = str(e)
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
        
        return result
    
    def refine_product(
        self,
        product_spec: Dict[str, Any],
        feedback: str
    ) -> Dict[str, Any]:
        """
        Refine an existing product based on user feedback
        
        Args:
            product_spec: Previously generated product
            feedback: User's refinement request
            
        Returns:
            Refined product specification
        """
        print("\n🔄 Refining product based on feedback...")
        print(f"   Feedback: {feedback}")
        print()
        
        refined_spec = self.schema_generator.refine_product(
            product_spec=product_spec,
            feedback=feedback
        )
        
        return refined_spec
    
    def _print_summary(self, result: Dict[str, Any]):
        """Print a summary of what was created"""
        spec = result.get("product_spec", {})
        prov = result.get("provisioning", {})
        
        print(f"\n📋 Product: {spec.get('product_name')}")
        print(f"   Type: {spec.get('product_type')}")
        print(f"   Owner: {spec.get('owner')}")
        
        if "kafka_config" in spec:
            kafka = spec["kafka_config"]
            print(f"\n📤 Kafka Topic: {kafka.get('topic_name')}")
            print(f"   Partitions: {kafka.get('partitions')}")
            print(f"   Retention: {kafka.get('retention_ms', 0) / 86400000:.1f} days")
        
        if "avro_schema" in spec:
            schema = spec["avro_schema"]
            print(f"\n📋 Schema: {schema.get('name')}")
            print(f"   Fields: {len(schema.get('fields', []))}")
        
        if "tags" in spec:
            print(f"\n🏷️  Tags: {', '.join(spec['tags'])}")
        
        if prov.get("steps"):
            print(f"\n🔧 Infrastructure:")
            for step, details in prov["steps"].items():
                status = details.get("status", "unknown")
                icon = "✅" if status in ["success", "created"] else "⚠️"
                print(f"   {icon} {step}: {status}")
        
        print()


def interactive_mode():
    """Interactive mode for creating products"""
    agent = ProductGeneratorAgent()
    
    print("🎨 INTERACTIVE PRODUCT CREATION MODE")
    print("=" * 70)
    print()
    
    # Get user input
    product_name = input("Product Name: ").strip()
    if not product_name:
        print("❌ Product name required")
        return
    
    owner = input("Owner (team or user): ").strip()
    if not owner:
        owner = "platform-team"
    
    print("\nDescribe what data product you need:")
    print("(Be as detailed as possible - include what data, how often, who uses it)")
    description = input("> ").strip()
    
    if not description:
        print("❌ Description required")
        return
    
    # Optional context
    print("\nOptional: Any additional requirements? (press Enter to skip)")
    context_input = input("> ").strip()
    
    additional_context = None
    if context_input:
        # Parse as key=value pairs
        try:
            additional_context = {}
            for pair in context_input.split(","):
                if "=" in pair:
                    key, value = pair.split("=", 1)
                    additional_context[key.strip()] = value.strip()
        except:
            print("⚠️  Could not parse context, continuing without it")
    
    # Generate
    print()
    result = agent.create_product_from_request(
        description=description,
        product_name=product_name,
        owner=owner,
        additional_context=additional_context,
        auto_provision=True
    )
    
    # Ask about refinement
    if result["success"]:
        print("\n💡 Would you like to refine this product? (y/n)")
        if input("> ").strip().lower() == 'y':
            feedback = input("What would you like to change? > ").strip()
            if feedback:
                refined = agent.refine_product(
                    result["product_spec"],
                    feedback
                )
                print("\n🔄 Refined specification:")
                print(json.dumps(refined, indent=2))


def example_usage():
    """Example usage with predefined requests"""
    agent = ProductGeneratorAgent()
    
    # Example 1: Supplier Performance
    print("\n📝 Example 1: Supplier Performance Metrics")
    print("-" * 70)
    
    result1 = agent.create_product_from_request(
        description="""
        I need a data product that tracks supplier performance metrics.
        It should include:
        - On-time delivery rate
        - Quality scores (defect rate)
        - Compliance status (certifications)
        - Response time metrics
        
        This should update daily and be used by procurement and quality teams.
        """,
        product_name="Supplier Performance Metrics",
        owner="procurement-team",
        additional_context={
            "industry": "food_supply_chain",
            "update_frequency": "daily",
            "consumers": ["procurement", "quality-assurance", "finance"]
        },
        auto_provision=True
    )
    
    # Example 2: Order Anomaly Detection
    print("\n📝 Example 2: Order Anomaly Detection Stream")
    print("-" * 70)
    
    result2 = agent.create_product_from_request(
        description="""
        Real-time stream that detects anomalies in order patterns.
        Should flag:
        - Unusual order quantities
        - Suspicious pricing
        - Geographic anomalies
        - Rapid repeat orders
        
        Needs to process orders in real-time with < 1 second latency.
        """,
        product_name="Order Anomaly Detection Stream",
        owner="fraud-prevention-team",
        additional_context={
            "latency_requirement": "< 1 second",
            "alert_channels": ["slack", "pagerduty"],
            "severity_levels": ["low", "medium", "high", "critical"]
        },
        auto_provision=True
    )
    
    # Save results
    with open("example_products.json", "w") as f:
        json.dump({
            "example1": result1,
            "example2": result2
        }, f, indent=2)
    
    print("\n💾 Results saved to example_products.json")


def main():
    """Main entry point"""
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--interactive":
        interactive_mode()
    elif len(sys.argv) > 1 and sys.argv[1] == "--examples":
        example_usage()
    else:
        print("""
Product Generator Agent - AI-Powered Data Product Creation

Usage:
  python main.py --interactive    # Interactive mode
  python main.py --examples       # Run example scenarios
  
Or import and use programmatically:
  from main import ProductGeneratorAgent
  agent = ProductGeneratorAgent()
  result = agent.create_product_from_request(...)
        """)


if __name__ == "__main__":
    main()
