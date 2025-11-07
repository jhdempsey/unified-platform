"""
Pydantic schemas for Product Service
Request/response validation and serialization
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator
from enum import Enum


class ProductType(str, Enum):
    """Types of data products"""
    DATASET = "DATASET"
    STREAM = "STREAM"
    API = "API"
    REPORT = "REPORT"
    ML_MODEL = "ML_MODEL"


class ProductBase(BaseModel):
    """Base product schema"""
    product_name: str = Field(..., min_length=1, max_length=200)
    product_type: ProductType
    owner: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=1000)
    schema_version: str = Field(default="1.0.0", pattern=r"^\d+\.\d+\.\d+$")
    schema_definition: Optional[Dict[str, Any]] = None
    tags: List[str] = Field(default_factory=list)
    quality_score: Optional[float] = Field(None, ge=0.0, le=100.0)
    kafka_topic: Optional[str] = Field(None, max_length=200)
    extra_metadata: Dict[str, Any] = Field(default_factory=dict)


class ProductCreate(ProductBase):
    """Schema for creating a product"""
    created_by: str = Field(..., min_length=1, max_length=100)
    
    @field_validator('tags')
    @classmethod
    def validate_tags(cls, v):
        """Validate tags are unique and lowercase"""
        return list(set([tag.lower().strip() for tag in v]))


class ProductUpdate(BaseModel):
    """Schema for updating a product"""
    product_name: Optional[str] = Field(None, min_length=1, max_length=200)
    product_type: Optional[ProductType] = None
    owner: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=1000)
    schema_version: Optional[str] = Field(None, pattern=r"^\d+\.\d+\.\d+$")
    schema_definition: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None
    quality_score: Optional[float] = Field(None, ge=0.0, le=100.0)
    kafka_topic: Optional[str] = Field(None, max_length=200)
    metadata: Optional[Dict[str, Any]] = None
    updated_by: str = Field(..., min_length=1, max_length=100)
    
    @field_validator('tags')
    @classmethod
    def validate_tags(cls, v):
        """Validate tags are unique and lowercase"""
        if v is not None:
            return list(set([tag.lower().strip() for tag in v]))
        return v


class ProductResponse(ProductBase):
    """Schema for product response"""
    product_id: str
    created_at: datetime
    updated_at: datetime
    created_by: str
    updated_by: Optional[str] = None
    
    class Config:
        from_attributes = True


class ProductList(BaseModel):
    """Schema for list of products"""
    products: List[ProductResponse]
    total: int
    page: int = 1
    page_size: int = 50


class ErrorResponse(BaseModel):
    """Error response schema"""
    error: str
    detail: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    version: str = "1.0.0"
    database: str = "connected"
    kafka: str = "connected"
