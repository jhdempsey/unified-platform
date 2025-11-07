"""
Database models for Product Service
SQLAlchemy models for data products
"""

from datetime import datetime
from typing import Optional, List
from sqlalchemy import Column, String, DateTime, Float, JSON, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
import enum

Base = declarative_base()


class ProductType(enum.Enum):
    """Types of data products"""
    DATASET = "DATASET"
    STREAM = "STREAM"
    API = "API"
    REPORT = "REPORT"
    ML_MODEL = "ML_MODEL"


class DataProduct(Base):
    """
    Data Product Model
    Represents a data product in the platform
    """
    __tablename__ = "data_products"
    
    # Primary Key
    product_id = Column(String(50), primary_key=True, index=True)
    
    # Basic Info
    product_name = Column(String(200), nullable=False, index=True)
    product_type = Column(SQLEnum(ProductType), nullable=False, index=True)
    owner = Column(String(100), nullable=False, index=True)
    description = Column(String(1000))
    
    # Schema & Versioning
    schema_version = Column(String(20), default="1.0.0")
    schema_definition = Column(JSON, nullable=True)
    
    # Metadata
    tags = Column(JSON, default=list)  # List of tags
    quality_score = Column(Float, nullable=True)
    
    # Kafka Integration
    kafka_topic = Column(String(200), nullable=True, index=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(100), nullable=False)
    updated_by = Column(String(100), nullable=True)
    
    # Additional metadata
    extra_metadata = Column(JSON, default=dict)
    
    def __repr__(self):
        return f"<DataProduct(id={self.product_id}, name={self.product_name}, type={self.product_type})>"
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            "product_id": self.product_id,
            "product_name": self.product_name,
            "product_type": self.product_type.value if self.product_type else None,
            "owner": self.owner,
            "description": self.description,
            "schema_version": self.schema_version,
            "schema_definition": self.schema_definition,
            "tags": self.tags or [],
            "quality_score": self.quality_score,
            "kafka_topic": self.kafka_topic,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "created_by": self.created_by,
            "updated_by": self.updated_by,
            "extra_metadata": self.metadata or {}
        }
