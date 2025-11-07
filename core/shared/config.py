"""
Centralized Configuration
All services import from here to avoid hardcoded values
"""

import os
from typing import Optional
from pathlib import Path


class PlatformConfig:
    """Platform-wide configuration from environment variables"""
    
    # ============================================================================
    # Service URLs
    # ============================================================================
    
    PRODUCT_SERVICE_URL: str = os.getenv(
        "PRODUCT_SERVICE_URL",
        "http://localhost:8001"
    )
    
    PRODUCT_GENERATOR_URL: str = os.getenv(
        "PRODUCT_GENERATOR_URL",
        "http://localhost:8003"
    )
    
    DISCOVERY_AGENT_URL: str = os.getenv(
        "DISCOVERY_AGENT_URL",
        "http://localhost:8004"
    )
    
    # ============================================================================
    # Infrastructure - Kafka
    # ============================================================================
    
    KAFKA_BOOTSTRAP_SERVERS: str = os.getenv(
        "KAFKA_BOOTSTRAP_SERVERS",
        "localhost:19093"
    )
    
    SCHEMA_REGISTRY_URL: str = os.getenv(
        "SCHEMA_REGISTRY_URL",
        "http://localhost:18081"
    )
    
    # ============================================================================
    # Infrastructure - Database
    # ============================================================================
    
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://platform:platform_dev@localhost:5432/platform"
    )
    
    REDIS_URL: str = os.getenv(
        "REDIS_URL",
        "redis://localhost:6380/0"
    )
    
    # ============================================================================
    # AI & External APIs
    # ============================================================================
    
    ANTHROPIC_API_KEY: Optional[str] = os.getenv("ANTHROPIC_API_KEY")
    
    # ============================================================================
    # Application Settings
    # ============================================================================
    
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Service Ports (for when services start themselves)
    PRODUCT_SERVICE_PORT: int = int(os.getenv("PRODUCT_SERVICE_PORT", "8001"))
    PRODUCT_GENERATOR_PORT: int = int(os.getenv("PRODUCT_GENERATOR_PORT", "8003"))
    DISCOVERY_AGENT_PORT: int = int(os.getenv("DISCOVERY_AGENT_PORT", "8004"))
    
    # ============================================================================
    # Paths
    # ============================================================================
    
    # Project root
    PROJECT_ROOT: Path = Path(__file__).parent.parent
    
    # Schema directories
    SCHEMA_DIR_GENERATED: Path = PROJECT_ROOT / "schemas" / "avro" / "generated"
    SCHEMA_DIR_MANUAL: Path = PROJECT_ROOT / "schemas" / "avro" / "manual"
    
    # ============================================================================
    # Kafka Configuration Defaults
    # ============================================================================
    
    KAFKA_DEFAULT_PARTITIONS: int = 3
    KAFKA_DEFAULT_REPLICATION_FACTOR: int = 1
    KAFKA_DEFAULT_RETENTION_MS: int = 604800000  # 7 days
    
    # ============================================================================
    # Service Discovery (for future use)
    # ============================================================================
    
    # If you add Consul/Eureka later
    SERVICE_DISCOVERY_ENABLED: bool = os.getenv(
        "SERVICE_DISCOVERY_ENABLED",
        "false"
    ).lower() == "true"
    
    SERVICE_DISCOVERY_URL: Optional[str] = os.getenv("SERVICE_DISCOVERY_URL")
    
    # ============================================================================
    # Observability
    # ============================================================================
    
    PROMETHEUS_PORT: int = int(os.getenv("PROMETHEUS_PORT", "9095"))
    GRAFANA_PORT: int = int(os.getenv("GRAFANA_PORT", "3002"))
    JAEGER_ENDPOINT: str = os.getenv(
        "JAEGER_ENDPOINT",
        "http://localhost:4318"
    )
    
    # ============================================================================
    # Helper Methods
    # ============================================================================
    
    @classmethod
    def is_production(cls) -> bool:
        """Check if running in production"""
        return cls.ENVIRONMENT.lower() == "production"
    
    @classmethod
    def is_development(cls) -> bool:
        """Check if running in development"""
        return cls.ENVIRONMENT.lower() == "development"
    
    @classmethod
    def get_service_url(cls, service_name: str) -> str:
        """
        Get service URL by name
        
        Args:
            service_name: 'product-service', 'product-generator', or 'discovery-agent'
            
        Returns:
            Service URL
        """
        service_map = {
            "product-service": cls.PRODUCT_SERVICE_URL,
            "product-generator": cls.PRODUCT_GENERATOR_URL,
            "discovery-agent": cls.DISCOVERY_AGENT_URL,
        }
        
        url = service_map.get(service_name)
        if not url:
            raise ValueError(f"Unknown service: {service_name}")
        
        return url
    
    @classmethod
    def validate(cls) -> None:
        """Validate required configuration"""
        errors = []
        
        # Check required values
        if not cls.ANTHROPIC_API_KEY:
            errors.append("ANTHROPIC_API_KEY not set")
        
        if not cls.DATABASE_URL:
            errors.append("DATABASE_URL not set")
        
        if errors:
            raise ValueError(f"Configuration errors: {', '.join(errors)}")
    
    @classmethod
    def print_config(cls) -> None:
        """Print current configuration (for debugging)"""
        print("=" * 70)
        print("🔧 Platform Configuration")
        print("=" * 70)
        print(f"Environment: {cls.ENVIRONMENT}")
        print(f"Log Level: {cls.LOG_LEVEL}")
        print("")
        print("Services:")
        print(f"  Product Service:     {cls.PRODUCT_SERVICE_URL}")
        print(f"  Product Generator:   {cls.PRODUCT_GENERATOR_URL}")
        print(f"  Discovery Agent:     {cls.DISCOVERY_AGENT_URL}")
        print("")
        print("Infrastructure:")
        print(f"  Kafka:              {cls.KAFKA_BOOTSTRAP_SERVERS}")
        print(f"  Schema Registry:    {cls.SCHEMA_REGISTRY_URL}")
        print(f"  Database:           {cls.DATABASE_URL.split('@')[1] if '@' in cls.DATABASE_URL else cls.DATABASE_URL}")
        print(f"  Redis:              {cls.REDIS_URL}")
        print("")
        print("AI:")
        print(f"  Anthropic API Key:  {'✅ Set' if cls.ANTHROPIC_API_KEY else '❌ Not Set'}")
        print("=" * 70)


# Singleton instance - import this
config = PlatformConfig()


if __name__ == "__main__":
    # Test configuration
    config.print_config()
    
    # Validate
    try:
        config.validate()
        print("\n✅ Configuration valid")
    except ValueError as e:
        print(f"\n❌ Configuration invalid: {e}")