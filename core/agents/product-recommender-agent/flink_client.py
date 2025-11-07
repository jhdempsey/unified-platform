"""
Flink REST API Client

Provides programmatic access to Flink cluster for:
- Job submission (SQL)
- Job monitoring
- Job cancellation
- Cluster health checks

Supports Flink REST API: https://nightlies.apache.org/flink/flink-docs-master/docs/ops/rest_api/
"""

import logging
import time
from typing import Dict, List, Optional, Any
from enum import Enum
import requests
from dataclasses import dataclass
import subprocess

logger = logging.getLogger(__name__)


class JobStatus(str, Enum):
    """Flink job status states"""
    CREATED = "CREATED"
    RUNNING = "RUNNING"
    FAILING = "FAILING"
    FAILED = "FAILED"
    CANCELLING = "CANCELLING"
    CANCELED = "CANCELED"
    FINISHED = "FINISHED"
    RESTARTING = "RESTARTING"
    SUSPENDED = "SUSPENDED"
    RECONCILING = "RECONCILING"


@dataclass
class FlinkJob:
    """Represents a Flink job"""
    job_id: str
    name: str
    status: JobStatus
    start_time: int
    end_time: Optional[int] = None
    duration: Optional[int] = None
    
    @property
    def is_running(self) -> bool:
        return self.status in [JobStatus.RUNNING, JobStatus.CREATED, JobStatus.RESTARTING]
    
    @property
    def is_terminal(self) -> bool:
        return self.status in [JobStatus.FINISHED, JobStatus.FAILED, JobStatus.CANCELED]


class FlinkClient:
    """
    Client for interacting with Flink REST API
    
    Args:
        base_url: Flink REST API base URL (default: http://localhost:8085)
        timeout: Request timeout in seconds (default: 30)
    """
    
    def __init__(
        self,
        base_url: str = "http://localhost:8085",
        timeout: int = 30
    ):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.session = requests.Session()
        
    def health_check(self) -> bool:
        """
        Check if Flink cluster is healthy
        
        Returns:
            True if cluster is accessible, False otherwise
        """
        try:
            response = self.session.get(
                f"{self.base_url}/overview",
                timeout=5
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Flink health check failed: {e}")
            return False
    
    def get_cluster_overview(self) -> Dict[str, Any]:
        """
        Get Flink cluster overview
        
        Returns:
            Cluster overview information
        """
        response = self.session.get(
            f"{self.base_url}/overview",
            timeout=self.timeout
        )
        response.raise_for_status()
        return response.json()
    
    def list_jobs(self) -> List[FlinkJob]:
        """
        List all jobs in the Flink cluster
        
        Returns:
            List of FlinkJob objects
        """
        response = self.session.get(
            f"{self.base_url}/jobs",
            timeout=self.timeout
        )
        response.raise_for_status()
        
        data = response.json()
        jobs = []
        
        for job_data in data.get("jobs", []):
            jobs.append(FlinkJob(
                job_id=job_data["id"],
                name=job_data.get("name", "Unknown"),
                status=JobStatus(job_data["status"]),
                start_time=job_data.get("start-time", 0),
                end_time=job_data.get("end-time"),
                duration=job_data.get("duration")
            ))
        
        return jobs
    
    def get_job(self, job_id: str) -> Optional[FlinkJob]:
        """
        Get details for a specific job
        
        Args:
            job_id: Flink job ID
            
        Returns:
            FlinkJob object or None if not found
        """
        try:
            response = self.session.get(
                f"{self.base_url}/jobs/{job_id}",
                timeout=self.timeout
            )
            response.raise_for_status()
            
            data = response.json()
            return FlinkJob(
                job_id=data["jid"],
                name=data.get("name", "Unknown"),
                status=JobStatus(data["state"]),
                start_time=data.get("start-time", 0),
                end_time=data.get("end-time"),
                duration=data.get("duration")
            )
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                return None
            raise
    
    def cancel_job(self, job_id: str) -> bool:
        """
        Cancel a running job
        
        Args:
            job_id: Flink job ID
            
        Returns:
            True if cancellation was successful
        """
        try:
            response = self.session.patch(
                f"{self.base_url}/jobs/{job_id}",
                timeout=self.timeout
            )
            response.raise_for_status()
            logger.info(f"Cancelled Flink job: {job_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to cancel job {job_id}: {e}")
            return False
    
    def submit_sql_via_client(self, sql_statements: str) -> Dict[str, Any]:
        """
        Submit SQL statements via Flink SQL Client container
        
        This is a workaround for programmatic SQL submission when SQL Gateway
        is not available. It executes SQL via the sql-client container.
        
        Args:
            sql_statements: SQL statements to execute
            
        Returns:
            Result dictionary with job_id if successful
        """
        try:
            # Create temporary SQL file
            sql_file = "/tmp/flink_job.sql"
            with open(sql_file, "w") as f:
                f.write(sql_statements)
            
            # Copy SQL file into container
            subprocess.run([
                "docker", "cp",
                sql_file,
                "platform-sql-client:/tmp/job.sql"
            ], check=True, capture_output=True)
            
            # Execute SQL via sql-client
            result = subprocess.run([
                "docker", "exec", "-i",
                "platform-sql-client",
                "./sql-client.sh", "-f", "/tmp/job.sql"
            ], capture_output=True, text=True, timeout=60)
            
            if result.returncode != 0:
                raise Exception(f"SQL execution failed: {result.stderr}")
            
            logger.info(f"SQL submitted successfully")
            logger.debug(f"Output: {result.stdout}")
            
            # Try to extract job ID from output (if statement was INSERT)
            # Format: "Job has been submitted with JobID <job_id>"
            job_id = None
            for line in result.stdout.split('\n'):
                if "JobID" in line or "Job ID" in line:
                    parts = line.split()
                    if parts:
                        job_id = parts[-1]
                        break
            
            return {
                "success": True,
                "job_id": job_id,
                "output": result.stdout
            }
            
        except subprocess.TimeoutExpired:
            raise Exception("SQL execution timed out after 60 seconds")
        except subprocess.CalledProcessError as e:
            raise Exception(f"Failed to execute SQL: {e.stderr}")
        except Exception as e:
            logger.error(f"SQL submission failed: {e}")
            raise
    
    def wait_for_job(
        self,
        job_id: str,
        timeout: int = 60,
        check_interval: int = 2
    ) -> FlinkJob:
        """
        Wait for a job to reach a terminal state
        
        Args:
            job_id: Job ID to wait for
            timeout: Maximum time to wait in seconds
            check_interval: Time between status checks in seconds
            
        Returns:
            Final FlinkJob state
            
        Raises:
            TimeoutError: If job doesn't reach terminal state within timeout
        """
        start_time = time.time()
        
        while (time.time() - start_time) < timeout:
            job = self.get_job(job_id)
            
            if job is None:
                raise ValueError(f"Job {job_id} not found")
            
            if job.is_terminal:
                return job
            
            logger.debug(f"Job {job_id} status: {job.status}")
            time.sleep(check_interval)
        
        raise TimeoutError(f"Job {job_id} did not complete within {timeout} seconds")
    
    def get_job_metrics(self, job_id: str) -> Dict[str, Any]:
        """
        Get metrics for a specific job
        
        Args:
            job_id: Flink job ID
            
        Returns:
            Job metrics
        """
        try:
            response = self.session.get(
                f"{self.base_url}/jobs/{job_id}/metrics",
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get metrics for job {job_id}: {e}")
            return {}
    
    def get_taskmanagers(self) -> List[Dict[str, Any]]:
        """
        Get list of TaskManagers
        
        Returns:
            List of TaskManager information
        """
        response = self.session.get(
            f"{self.base_url}/taskmanagers",
            timeout=self.timeout
        )
        response.raise_for_status()
        return response.json().get("taskmanagers", [])


# Convenience functions for common operations

def create_flink_client(base_url: str = "http://localhost:8085") -> FlinkClient:
    """
    Create and validate Flink client
    
    Args:
        base_url: Flink REST API URL
        
    Returns:
        FlinkClient instance
        
    Raises:
        ConnectionError: If cannot connect to Flink
    """
    client = FlinkClient(base_url)
    
    if not client.health_check():
        raise ConnectionError(f"Cannot connect to Flink at {base_url}")
    
    return client


def submit_sql(sql: str, client: Optional[FlinkClient] = None) -> Dict[str, Any]:
    """
    Submit SQL statements to Flink
    
    Args:
        sql: SQL statements to execute
        client: FlinkClient instance (creates new one if not provided)
        
    Returns:
        Submission result with job_id
    """
    if client is None:
        client = create_flink_client()
    
    return client.submit_sql_via_client(sql)


if __name__ == "__main__":
    # Example usage and testing
    logging.basicConfig(level=logging.INFO)
    
    print("🌊 Testing Flink Client")
    print("=" * 60)
    
    try:
        # Create client
        print("\n1. Creating Flink client...")
        client = create_flink_client()
        print("   ✅ Connected to Flink")
        
        # Get cluster overview
        print("\n2. Getting cluster overview...")
        overview = client.get_cluster_overview()
        print(f"   TaskManagers: {overview.get('taskmanagers')}")
        print(f"   Slots Total: {overview.get('slots-total')}")
        print(f"   Slots Available: {overview.get('slots-available')}")
        
        # List jobs
        print("\n3. Listing jobs...")
        jobs = client.list_jobs()
        if jobs:
            for job in jobs:
                print(f"   {job.job_id[:8]}... - {job.name} [{job.status}]")
        else:
            print("   No jobs running")
        
        print("\n✅ Flink client working!")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")