"""
Database configuration and session management.

This module provides SQLAlchemy engine, session factory, and declarative base
for ORM models. Supports both Postgres (production) and SQLite (testing).
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Read database URL from environment
# Priority: DATABASE_URL (production) > TEST_DATABASE_URL (testing) > sqlite (fallback)
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    os.getenv(
        "TEST_DATABASE_URL",
        "sqlite:///./test.db"  # Fallback for local development
    )
)

# Create engine with appropriate settings
if DATABASE_URL.startswith("sqlite"):
    # SQLite-specific settings
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},  # Allow multi-threading
        echo=False  # Set to True for SQL query logging
    )
else:
    # PostgreSQL settings
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,  # Verify connections before using
        echo=False
    )

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Declarative base for ORM models
Base = declarative_base()


def get_db():
    """
    Dependency function for FastAPI routes.

    Yields a database session and ensures it's properly closed.

    Usage in FastAPI:
        @router.get("/items")
        def get_items(db: Session = Depends(get_db)):
            return db.query(Item).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
