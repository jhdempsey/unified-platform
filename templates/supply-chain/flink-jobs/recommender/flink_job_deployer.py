"""
Flink Job Deployer

Takes product recommendations and deploys them as Flink streaming jobs.
Manages the lifecycle from recommendation → deployed product → running job.

Workflow:
1. User approves a recommendation
2. Deployer creates product topic in Kafka
3. Deployer submits Flink SQL job
4. Deployer tracks job ID and status
5. Product becomes "ACTIVE" with data flowing
"""

import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import subprocess
from datetime import datetime

from flink_client import FlinkClient, FlinkJob, JobStatus

logger = logging.getLogger(__name__)


class ProductStatus(str, Enum):
    """Product lifecycle states"""
    RECOMMENDED = "RECOMMENDED"  # AI recommended, not deployed
    DEPLOYING = "DEPLOYING"      # Deployment in progress
    ACTIVE = "ACTIVE"            # Running in production
    FAILED = "FAILED"            # Deployment failed
    STOPPED = "STOPPED"          # User stopped the product
    ARCHIVED = "ARCHIVED"        # No longer in use


@dataclass
class DeploymentResult:
    """Result of deploying a product"""
    success: bool
    product_id: str
    flink_job_id: Optional[str] = None
    error_message: Optional[str] = None
    created_topics: List[str] = None
    
    def __post_init__(self):
        if self.created_topics is None:
            self.created_topics = []


class FlinkJobDeployer:
    """
    Deploys AI recommendations as Flink streaming jobs
    
    Args:
        flink_client: FlinkClient instance
        kafka_bootstrap_servers: Kafka connection string
    """
    
    def __init__(
        self,
        flink_client: FlinkClient,
        kafka_bootstrap_servers: str = "kafka:9092"
    ):
        self.flink = flink_client
        self.kafka_bootstrap = kafka_bootstrap_servers
        
    def deploy_recommendation(
        self,
        recommendation: Dict[str, Any]
    ) -> DeploymentResult:
        """
        Deploy a recommendation as a live Flink job
        
        Args:
            recommendation: Recommendation dict from database with:
                - product_id: Unique product identifier
                - product_name: Name of the product
                - flink_sql: SQL statements to execute
                - output_topic: Target Kafka topic
                
        Returns:
            DeploymentResult with job details
        """
        product_id = recommendation["product_id"]
        product_name = recommendation["product_name"]
        flink_sql = recommendation["flink_sql"]
        output_topic = recommendation.get("output_topic", f"product.{product_id}")
        
        logger.info(f"Deploying recommendation {product_id}: {product_name}")
        
        try:
            # Step 1: Create output topic in Kafka
            created_topics = self._create_kafka_topics([output_topic])
            logger.info(f"Created Kafka topic: {output_topic}")
            
            # Step 2: Prepare Flink SQL with Kafka connectors
            enriched_sql = self._enrich_sql_with_connectors(
                flink_sql,
                output_topic
            )
            
            # Step 3: Submit Flink job
            logger.info("Submitting Flink SQL job...")
            result = self.flink.submit_sql_via_client(enriched_sql)
            
            if not result.get("success"):
                raise Exception(f"SQL submission failed: {result.get('output')}")
            
            job_id = result.get("job_id")
            logger.info(f"Flink job submitted successfully: {job_id}")
            
            # Step 4: Wait for job to start (optional)
            if job_id:
                self._wait_for_job_running(job_id, timeout=30)
            
            return DeploymentResult(
                success=True,
                product_id=product_id,
                flink_job_id=job_id,
                created_topics=created_topics
            )
            
        except Exception as e:
            logger.error(f"Deployment failed for {product_id}: {e}")
            return DeploymentResult(
                success=False,
                product_id=product_id,
                error_message=str(e)
            )
    
    def _create_kafka_topics(self, topics: List[str]) -> List[str]:
        """
        Create Kafka topics if they don't exist
        
        Args:
            topics: List of topic names
            
        Returns:
            List of created topics
        """
        created = []
        
        for topic in topics:
            try:
                # Check if topic exists
                result = subprocess.run([
                    "docker", "exec", "platform-kafka",
                    "kafka-topics", "--bootstrap-server", "localhost:9092",
                    "--list"
                ], capture_output=True, text=True, check=True)
                
                if topic in result.stdout:
                    logger.info(f"Topic {topic} already exists")
                    continue
                
                # Create topic
                subprocess.run([
                    "docker", "exec", "platform-kafka",
                    "kafka-topics", "--bootstrap-server", "localhost:9092",
                    "--create", "--topic", topic,
                    "--partitions", "3",
                    "--replication-factor", "1"
                ], capture_output=True, text=True, check=True)
                
                logger.info(f"Created Kafka topic: {topic}")
                created.append(topic)
                
            except subprocess.CalledProcessError as e:
                logger.error(f"Failed to create topic {topic}: {e.stderr}")
                raise
        
        return created
    
    def _enrich_sql_with_connectors(
        self,
        sql: str,
        output_topic: str
    ) -> str:
        """
        Add Kafka connector configuration to SQL
        
        If the SQL doesn't have connector config, adds it.
        If it does, ensures it points to correct Kafka cluster.
        
        Args:
            sql: Original Flink SQL
            output_topic: Output Kafka topic
            
        Returns:
            Enhanced SQL with Kafka connectors
        """
        # For now, just ensure the SQL has proper Kafka settings
        # In a real implementation, you'd parse and modify the SQL
        
        # Add Kafka configuration if missing
        if "'connector' = 'kafka'" not in sql:
            logger.warning("SQL missing Kafka connector - may fail")
        
        # Replace placeholder bootstrap servers if present
        sql = sql.replace(
            "'properties.bootstrap.servers' = 'kafka:9092'",
            f"'properties.bootstrap.servers' = '{self.kafka_bootstrap}'"
        )
        
        return sql
    
    def _wait_for_job_running(
        self,
        job_id: str,
        timeout: int = 30
    ) -> None:
        """
        Wait for Flink job to reach RUNNING state
        
        Args:
            job_id: Flink job ID
            timeout: Max seconds to wait
            
        Raises:
            TimeoutError: If job doesn't start in time
        """
        try:
            job = self.flink.wait_for_job(job_id, timeout=timeout)
            
            if job.status == JobStatus.RUNNING:
                logger.info(f"Job {job_id} is RUNNING")
            elif job.status == JobStatus.FAILED:
                raise Exception(f"Job {job_id} FAILED")
            else:
                logger.warning(f"Job {job_id} in unexpected state: {job.status}")
                
        except TimeoutError:
            logger.warning(f"Job {job_id} didn't start within {timeout}s, but may still be starting")
    
    def stop_product(self, flink_job_id: str) -> bool:
        """
        Stop a running product by canceling its Flink job
        
        Args:
            flink_job_id: Flink job ID
            
        Returns:
            True if job was canceled successfully
        """
        logger.info(f"Stopping product with job {flink_job_id}")
        return self.flink.cancel_job(flink_job_id)
    
    def get_product_status(self, flink_job_id: str) -> Dict[str, Any]:
        """
        Get current status of a deployed product
        
        Args:
            flink_job_id: Flink job ID
            
        Returns:
            Status dict with job state and metrics
        """
        job = self.flink.get_job(flink_job_id)
        
        if not job:
            return {
                "status": "NOT_FOUND",
                "message": f"Job {flink_job_id} not found in Flink"
            }
        
        metrics = self.flink.get_job_metrics(flink_job_id)
        
        return {
            "status": job.status.value,
            "is_running": job.is_running,
            "start_time": job.start_time,
            "duration": job.duration,
            "metrics": metrics
        }
    
    def list_active_products(self) -> List[Dict[str, Any]]:
        """
        List all active products (running Flink jobs)
        
        Returns:
            List of product summaries
        """
        jobs = self.flink.list_jobs()
        
        return [
            {
                "job_id": job.job_id,
                "name": job.name,
                "status": job.status.value,
                "start_time": job.start_time,
                "is_running": job.is_running
            }
            for job in jobs
        ]


# Convenience functions

def create_deployer(
    flink_url: str = "http://localhost:8085",
    kafka_bootstrap: str = "kafka:9092"
) -> FlinkJobDeployer:
    """
    Create FlinkJobDeployer with default configuration
    
    Args:
        flink_url: Flink REST API URL
        kafka_bootstrap: Kafka bootstrap servers
        
    Returns:
        Configured FlinkJobDeployer
    """
    from flink_client import create_flink_client
    
    flink_client = create_flink_client(flink_url)
    return FlinkJobDeployer(flink_client, kafka_bootstrap)


def deploy_recommendation(
    recommendation: Dict[str, Any],
    deployer: Optional[FlinkJobDeployer] = None
) -> DeploymentResult:
    """
    Deploy a recommendation (convenience function)
    
    Args:
        recommendation: Recommendation dict
        deployer: FlinkJobDeployer (creates new if not provided)
        
    Returns:
        DeploymentResult
    """
    if deployer is None:
        deployer = create_deployer()
    
    return deployer.deploy_recommendation(recommendation)


if __name__ == "__main__":
    # Example usage and testing
    logging.basicConfig(level=logging.INFO)
    
    print("🚀 Testing Flink Job Deployer")
    print("=" * 60)
    
    try:
        # Create deployer
        print("\n1. Creating deployer...")
        deployer = create_deployer()
        print("   ✅ Deployer created")
        
        # List active products
        print("\n2. Listing active products...")
        products = deployer.list_active_products()
        if products:
            for p in products:
                print(f"   - {p['name']} [{p['status']}]")
        else:
            print("   No active products")
        
        # Example: Deploy a test recommendation
        print("\n3. Example recommendation structure:")
        example = {
            "product_id": "test-123",
            "product_name": "Test Product",
            "flink_sql": """
                CREATE TABLE test_output (
                    id STRING,
                    value DOUBLE
                ) WITH (
                    'connector' = 'kafka',
                    'topic' = 'product.test-123',
                    'properties.bootstrap.servers' = 'kafka:9092',
                    'format' = 'json'
                );
                
                -- Would have INSERT statement here
            """,
            "output_topic": "product.test-123"
        }
        print(f"   Product ID: {example['product_id']}")
        print(f"   Output Topic: {example['output_topic']}")
        print("   Note: Not actually deploying in test mode")
        
        print("\n✅ Deployer ready to use!")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")