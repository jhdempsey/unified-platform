"""
CRUD operations for data products
Create, Read, Update, Delete operations
"""

import uuid
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_

from models import DataProduct, ProductType as DBProductType
from schemas import ProductCreate, ProductUpdate, ProductType


def generate_product_id() -> str:
    """Generate unique product ID"""
    return f"PROD-{uuid.uuid4().hex[:8].upper()}"


def create_product(db: Session, product: ProductCreate) -> DataProduct:
    """
    Create a new data product
    
    Args:
        db: Database session
        product: Product data
        
    Returns:
        Created product
    """
    # Generate unique ID
    product_id = generate_product_id()
    
    # Convert enum
    product_type_enum = DBProductType[product.product_type.value]
    
    # Create database model
    db_product = DataProduct(
        product_id=product_id,
        product_name=product.product_name,
        product_type=product_type_enum,
        owner=product.owner,
        description=product.description,
        schema_version=product.schema_version,
        schema_definition=product.schema_definition,
        tags=product.tags,
        quality_score=product.quality_score,
        kafka_topic=product.kafka_topic,
        created_by=product.created_by,
        extra_metadata=product.extra_metadata
    )
    
    # Add and commit
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    
    return db_product


def get_product(db: Session, product_id: str) -> Optional[DataProduct]:
    """
    Get a product by ID
    
    Args:
        db: Database session
        product_id: Product ID
        
    Returns:
        Product or None
    """
    return db.query(DataProduct).filter(DataProduct.product_id == product_id).first()


def get_products(
    db: Session,
    skip: int = 0,
    limit: int = 50,
    product_type: Optional[ProductType] = None,
    owner: Optional[str] = None,
    search: Optional[str] = None,
    tags: Optional[List[str]] = None
) -> tuple[List[DataProduct], int]:
    """
    Get list of products with filters
    
    Args:
        db: Database session
        skip: Number of records to skip
        limit: Maximum records to return
        product_type: Filter by product type
        owner: Filter by owner
        search: Search in name and description
        tags: Filter by tags
        
    Returns:
        Tuple of (products, total_count)
    """
    query = db.query(DataProduct)
    
    # Apply filters
    if product_type:
        product_type_enum = DBProductType[product_type.value]
        query = query.filter(DataProduct.product_type == product_type_enum)
    
    if owner:
        query = query.filter(DataProduct.owner == owner)
    
    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            or_(
                DataProduct.product_name.ilike(search_filter),
                DataProduct.description.ilike(search_filter)
            )
        )
    
    if tags:
        # Filter products that have any of the specified tags
        for tag in tags:
            query = query.filter(DataProduct.tags.contains([tag.lower()]))
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    products = query.order_by(DataProduct.created_at.desc()).offset(skip).limit(limit).all()
    
    return products, total


def update_product(
    db: Session,
    product_id: str,
    product_update: ProductUpdate
) -> Optional[DataProduct]:
    """
    Update a product
    
    Args:
        db: Database session
        product_id: Product ID
        product_update: Update data
        
    Returns:
        Updated product or None
    """
    db_product = get_product(db, product_id)
    
    if not db_product:
        return None
    
    # Update fields
    update_data = product_update.model_dump(exclude_unset=True)
    
    # Convert enum if present
    if "product_type" in update_data:
        update_data["product_type"] = DBProductType[update_data["product_type"].value]
    
    for field, value in update_data.items():
        setattr(db_product, field, value)
    
    db.commit()
    db.refresh(db_product)
    
    return db_product


def delete_product(db: Session, product_id: str) -> bool:
    """
    Delete a product
    
    Args:
        db: Database session
        product_id: Product ID
        
    Returns:
        True if deleted, False if not found
    """
    db_product = get_product(db, product_id)
    
    if not db_product:
        return False
    
    db.delete(db_product)
    db.commit()
    
    return True


def get_products_by_kafka_topic(db: Session, topic: str) -> List[DataProduct]:
    """
    Get products associated with a Kafka topic
    
    Args:
        db: Database session
        topic: Kafka topic name
        
    Returns:
        List of products
    """
    return db.query(DataProduct).filter(DataProduct.kafka_topic == topic).all()


def get_product_stats(db: Session) -> dict:
    """
    Get statistics about products
    
    Returns:
        Statistics dictionary
    """
    total = db.query(DataProduct).count()
    
    # Count by type
    by_type = {}
    for product_type in DBProductType:
        count = db.query(DataProduct).filter(
            DataProduct.product_type == product_type
        ).count()
        by_type[product_type.value] = count
    
    return {
        "total_products": total,
        "by_type": by_type
    }
