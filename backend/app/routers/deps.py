"""
Dependency injection helpers for FastAPI routes.
"""
from typing import Generator
from sqlalchemy.orm import Session
from app.database import SessionLocal


def get_db() -> Generator[Session, None, None]:
    """
    Database session dependency for FastAPI routes.

    Yields:
        Session: SQLAlchemy database session

    Usage:
        @router.get("/example")
        def example_route(db: Session = Depends(get_db)):
            # Use db session here
            pass
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
