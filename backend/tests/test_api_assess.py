"""
Basic API health check tests.

Note: Assessment endpoint tests have been moved to tests/assessments/test_assess_api.py
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base
from app.routers.deps import get_db


# Test database setup (SQLite using a file for persistence across connections)
TEST_DATABASE_URL = "sqlite:///./test_api.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override get_db dependency for tests."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


# Apply dependency override
app.dependency_overrides[get_db] = override_get_db

# Create tables at module level - MUST happen after Base and models are imported
Base.metadata.drop_all(bind=engine)  # Clean start
Base.metadata.create_all(bind=engine)


@pytest.fixture
def client():
    """FastAPI test client fixture."""
    with TestClient(app) as c:
        yield c


def test_health_endpoint(client):
    """Test that /health returns ok status."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"ok": True}


def test_root_endpoint(client):
    """Test that root / returns ok status."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"ok": True}
