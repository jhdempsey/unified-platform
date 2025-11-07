"""
Database configuration
SQLAlchemy setup and session management
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from contextlib import contextmanager
from typing import Generator

from models import Base


# Database URL from environment
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://platform:platform_dev@localhost:5432/platform"
)

# Create engine
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # Verify connections before using
    echo=False  # Set to True for SQL debugging
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Initialize database - create all tables"""
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created")


def get_db() -> Generator[Session, None, None]:
    """
    Dependency for FastAPI
    Provides database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_session():
    """
    Context manager for database session
    Use in non-FastAPI contexts
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    # Test database connection
    print(f"Testing connection to: {DATABASE_URL}")
    try:
        init_db()
        with get_db_session() as db:
            result = db.execute("SELECT 1")
            print(f"✅ Database connection successful: {result.fetchone()}")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
