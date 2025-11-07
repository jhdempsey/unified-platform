"""
Product Provisioner
Automatically provisions all infrastructure for a data product
"""

import os
import json
from typing import Dict, Any, Optional
from pathlib import Path

from confluent_kafka.admin import AdminClient, NewTopic
from confluent_kafka.schema_registry import SchemaRegistryClient, Schema

from shared.config import config

class ProductProvisioner:
    """
    Provisions infrastructure for data products:
    - Creates Kafka topics
    - Registers Avro schemas
    - Saves schema files
    - Creates product in database
    """
    
    def __init__(
        self,
        kafka_bootstrap_servers: str = None,
        schema_registry_url: str = None,
        schema_dir: str = None,
        product_service_url: str = None
    ):
        """Initialize provisioner"""
        self.kafka_bootstrap_servers = kafka_bootstrap_servers or config.KAFKA_BOOTSTRAP_SERVERS
        self.schema_registry_url = schema_registry_url or config.SCHEMA_REGISTRY_URL
        self.product_service_url = product_service_url or config.PRODUCT_SERVICE_URL
        self.schema_dir = Path(schema_dir or config.SCHEMA_DIR_GENERATED)
         
        # Ensure schema directory exists
        self.schema_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize clients
        self.admin_client = AdminClient({
            'bootstrap.servers': self.kafka_bootstrap_servers
        })
        
        self.schema_registry_client = SchemaRegistryClient({
            'url': self.schema_registry_url
        })
    
    def provision_product(
        self,
        product_spec: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Provision complete infrastructure for a data product
        
        Args:
            product_spec: Product specification from SchemaGenerator
            
        Returns:
            Provisioning results with status of each step
        """
        results = {
            "product_name": product_spec.get("product_name"),
            "steps": {},
            "success": False
        }
        
        print(f"\n🔧 Provisioning product: {product_spec['product_name']}")
        
        try:
            # Step 1: Save schema file
            schema_file = self._save_schema_file(product_spec)
            results["steps"]["schema_file"] = {
                "status": "success",
                "path": str(schema_file)
            }
            print(f"  ✅ Schema saved: {schema_file.name}")
            
            # Step 2: Create Kafka topic
            topic_result = self._create_kafka_topic(product_spec["kafka_config"])
            results["steps"]["kafka_topic"] = topic_result
            print(f"  ✅ Kafka topic: {product_spec['kafka_config']['topic_name']}")
            
            # Step 3: Register schema
            schema_id = self._register_schema(
                product_spec["kafka_config"]["topic_name"],
                product_spec["avro_schema"]
            )
            results["steps"]["schema_registry"] = {
                "status": "success",
                "schema_id": schema_id
            }
            print(f"  ✅ Schema registered: ID {schema_id}")
            
            # Step 4: Create product in database (if Product Service is available)
            product_id = self._create_product_record(product_spec)
            if product_id:
                results["steps"]["database"] = {
                    "status": "success",
                    "product_id": product_id
                }
                print(f"  ✅ Product created: {product_id}")
            
            results["success"] = True
            print(f"\n🎉 Product provisioned successfully!")
            
        except Exception as e:
            results["error"] = str(e)
            print(f"\n❌ Provisioning failed: {e}")
        
        return results
    
    def _save_schema_file(self, product_spec: Dict[str, Any]) -> Path:
        """Save Avro schema to file"""
        # Generate filename from product name
        filename = product_spec["product_name"].lower().replace(" ", "-") + ".avsc"
        filepath = self.schema_dir / filename
        
        # Write schema
        with open(filepath, 'w') as f:
            json.dump(product_spec["avro_schema"], f, indent=2)
        
        return filepath
    
    def _create_kafka_topic(self, kafka_config: Dict[str, Any]) -> Dict[str, Any]:
        """Create Kafka topic"""
        topic_name = kafka_config["topic_name"]
        
        # Check if topic exists
        metadata = self.admin_client.list_topics(timeout=10)
        if topic_name in metadata.topics:
            return {
                "status": "already_exists",
                "topic": topic_name
            }
        
        # Create topic
        new_topic = NewTopic(
            topic=topic_name,
            num_partitions=kafka_config.get("partitions", 3),
            replication_factor=min(kafka_config.get("replication_factor", 1), 1),  # Local dev = 1
            config={
                "retention.ms": str(kafka_config.get("retention_ms", 604800000)),
                "cleanup.policy": kafka_config.get("cleanup_policy", "delete")
            }
        )
        
        futures = self.admin_client.create_topics([new_topic])
        
        # Wait for creation
        for topic, future in futures.items():
            try:
                future.result()
                return {
                    "status": "created",
                    "topic": topic_name,
                    "partitions": kafka_config.get("partitions", 3)
                }
            except Exception as e:
                return {
                    "status": "error",
                    "error": str(e)
                }
    
    def _register_schema(
        self,
        topic_name: str,
        avro_schema: Dict[str, Any]
    ) -> int:
        """Register schema in Schema Registry"""
        subject = f"{topic_name}-value"
        schema_str = json.dumps(avro_schema)
        
        schema = Schema(schema_str, schema_type="AVRO")
        schema_id = self.schema_registry_client.register_schema(
            subject_name=subject,
            schema=schema
        )
        
        return schema_id
    
    def _create_product_record(self, product_spec: Dict[str, Any]) -> Optional[str]:
        """Create product record via Product Service API"""
        try:
            import requests
            
            # Prepare product data
            product_data = {
                "product_name": product_spec["product_name"],
                "product_type": product_spec["product_type"],
                "owner": product_spec["owner"],
                "description": product_spec.get("description_enhanced", ""),
                "schema_version": "1.0.0",
                "schema_definition": product_spec["avro_schema"],
                "tags": product_spec.get("tags", []),
                "kafka_topic": product_spec["kafka_config"]["topic_name"],
                "quality_score": None,
                "extra_metadata": {
                    "data_sources": product_spec.get("data_sources", []),
                    "transformations": product_spec.get("transformations", []),
                    "quality_rules": product_spec.get("quality_rules", []),
                    "estimated_volume": product_spec.get("estimated_volume", {}),
                    "sla": product_spec.get("sla", {})
                },
                "created_by": "AI_AGENT"
            }
            
            # Call Product Service
            url = f"{self.product_service_url}/products"
            response = requests.post(url, json=product_data, timeout=10)
            
            if response.status_code == 201:
                return response.json()["product_id"]
            else:
                print(f"  ⚠️  Product Service returned: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"  ⚠️  Could not create product record: {e}")
            return None
    
    def deprovision_product(self, topic_name: str) -> Dict[str, Any]:
        """
        Remove provisioned infrastructure
        (Use with caution in production!)
        """
        results = {
            "topic_name": topic_name,
            "steps": {}
        }
        
        print(f"\n🗑️  Deprovisioning: {topic_name}")
        
        # Delete topic (commented out for safety)
        # futures = self.admin_client.delete_topics([topic_name])
        # for topic, future in futures.items():
        #     try:
        #         future.result()
        #         results["steps"]["topic_deleted"] = {"status": "success"}
        #     except Exception as e:
        #         results["steps"]["topic_deleted"] = {"status": "error", "error": str(e)}
        
        print(f"  ℹ️  Topic deletion disabled for safety")
        print(f"  ℹ️  To delete: kafka-topics --delete --topic {topic_name}")
        
        return results


if __name__ == "__main__":
    # Test provisioner
    provisioner = ProductProvisioner()
    
    # Sample product spec
    product_spec = {
        "product_name": "Test Product",
        "product_type": "DATASET",
        "owner": "test-team",
        "description_enhanced": "Test data product",
        "avro_schema": {
            "type": "record",
            "name": "TestProduct",
            "namespace": "com.platform.products",
            "fields": [
                {"name": "id", "type": "string"},
                {"name": "value", "type": "double"}
            ]
        },
        "kafka_config": {
            "topic_name": "test-product",
            "partitions": 2,
            "replication_factor": 1,
            "retention_ms": 86400000,
            "cleanup_policy": "delete"
        },
        "tags": ["test"]
    }
    
    results = provisioner.provision_product(product_spec)
    print("\nResults:")
    print(json.dumps(results, indent=2))
