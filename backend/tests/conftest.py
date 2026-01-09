"""
Shared test fixtures for all tests.

Provides database setup, test client, and authentication helpers.
"""
import os
# Set TESTING environment variable before importing app to skip migrations
os.environ["TESTING"] = "true"

import warnings
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

# Suppress passlib deprecation warning
warnings.filterwarnings("ignore", category=DeprecationWarning, module="passlib")

from app.main import app
from app.database import Base
from app.models import User, Organization
from app.routers.deps import get_db
from app.core.jwt_tokens import create_access_token
from app.core.passwords import hash_password


@pytest.fixture(scope="function")
def db_engine():
    """
    Create a file-based SQLite engine for testing.
    
    Creates fresh database schema for each test function.
    Uses file-based DB to allow multiple connections to share the same database.
    """
    import tempfile
    import os
    
    # Create temporary database file
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    
    engine = create_engine(
        f"sqlite:///{db_path}",
        echo=False,
        connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)
    engine.dispose()
    
    # Clean up temp file
    try:
        os.unlink(db_path)
    except:
        pass


@pytest.fixture(scope="function")
def db_session(db_engine):
    """
    Create a database session for each test.
    
    Automatically rolls back after each test to keep tests isolated.
    """
    Session = sessionmaker(bind=db_engine)
    session = Session()
    yield session
    session.rollback()
    session.close()


@pytest.fixture(scope="function")
def test_client(db_engine):
    """
    Create a FastAPI TestClient with database override.
    
    Routes database calls to the test database using the same engine.
    """
    TestingSessionLocal = sessionmaker(bind=db_engine)
    
    def override_get_db():
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            session.close()
    
    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def sample_organization(db_session: Session) -> Organization:
    """
    Create a sample organization for tests.
    
    Returns:
        Organization object with name='Test Organization'
    """
    org = Organization(
        name="Test Organization",
        description="Organization for testing",
        is_active=True,
    )
    db_session.add(org)
    db_session.commit()
    db_session.refresh(org)
    return org


@pytest.fixture(scope="function")
def sample_user(db_session: Session, sample_organization: Organization) -> User:
    """
    Create a sample user for authentication tests.
    
    Returns:
        User object with email='test@example.com' and password='testpass123'
    """
    user = User(
        email="test@example.com",
        hashed_password=hash_password("testpass123"),
        full_name="Test User",
        is_active=True,
        is_superuser=False,
        organization_id=sample_organization.id,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
def auth_headers(sample_user: User) -> dict:
    """
    Generate authentication headers with valid JWT token.
    
    Returns:
        Dict with Authorization header containing Bearer token
    """
    access_token = create_access_token(sub=sample_user.email)
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture(scope="function")
def sample_prompt_template(db_session: Session, sample_organization: Organization):
    """
    Create a default prompt template for the test organization.
    
    This is required for assessment/scoring tests as the scorer service
    needs an active prompt template for the organization.
    
    Returns:
        PromptTemplate object (v0, active)
    """
    from app.crud import prompt_template as template_crud
    
    template = template_crud.create_default_for_org(
        db_session,
        sample_organization.id
    )
    return template


@pytest.fixture(scope="function")
def second_organization(db_session: Session) -> Organization:
    """
    Create a second organization for cross-org testing.
    
    Returns:
        Organization object with name='Second Organization'
    """
    org = Organization(
        name="Second Organization",
        description="Second organization for testing cross-org isolation",
        is_active=True,
    )
    db_session.add(org)
    db_session.commit()
    db_session.refresh(org)
    return org


@pytest.fixture(scope="function")
def second_user(db_session: Session, second_organization: Organization) -> User:
    """
    Create a user in the second organization for cross-org testing.
    
    Returns:
        User object with email='second@example.com' and password='testpass123'
    """
    user = User(
        email="second@example.com",
        hashed_password=hash_password("testpass123"),
        full_name="Second User",
        is_active=True,
        is_superuser=False,
        organization_id=second_organization.id,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
def second_auth_headers(second_user: User) -> dict:
    """
    Generate authentication headers for the second user with valid JWT token.
    
    Returns:
        Dict with Authorization header containing Bearer token for second user
    """
    access_token = create_access_token(sub=second_user.email)
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture(scope="function")
def admin_user(db_session: Session, sample_organization: Organization) -> User:
    """
    Create an admin/superuser for admin-only endpoint tests.
    
    Returns:
        User object with email='admin@example.com', password='adminpass123', and is_superuser=True
    """
    user = User(
        email="admin@example.com",
        hashed_password=hash_password("adminpass123"),
        full_name="Admin User",
        is_active=True,
        is_superuser=True,
        organization_id=sample_organization.id,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
def admin_auth_headers(admin_user: User) -> dict:
    """
    Generate authentication headers for admin user with valid JWT token.
    
    Returns:
        Dict with Authorization header containing Bearer token for admin user
    """
    access_token = create_access_token(sub=admin_user.email)
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture(scope="function")
def sample_llm_credential(db_session: Session, sample_organization: Organization):
    """
    Create a sample LLM credential for testing.
    
    Returns:
        LLMCredential object with OpenAI provider and test API key
    """
    from app.crud import llm_credential as cred_crud
    from app.models.llm_credential import LLMProvider
    
    return cred_crud.create(
        db_session,
        organization_id=sample_organization.id,
        provider=LLMProvider.OPENAI,
        api_key="sk-test1234567890abcdef",
        default_model="gpt-4o-mini"
    )


@pytest.fixture(scope="function")
def sample_evaluation_dataset(db_session: Session, sample_organization: Organization, tmp_path):
    """
    Create a sample evaluation dataset with CSV file.
    
    Returns:
        EvaluationDataset object with name='Test Dataset' and 2 examples
    """
    from app.crud import evaluation_dataset as dataset_crud
    
    # Create CSV file
    csv_content = """id,transcript,score_situation,score_problem,score_implication,score_need_payoff,score_flow,score_tone,score_engagement
1,"Rep: Hello\\nBuyer: Hi",4,3,4,3,4,4,3
2,"Rep: How are you?\\nBuyer: Good",3,4,3,4,3,4,4
"""
    csv_path = tmp_path / "test_dataset.csv"
    csv_path.write_text(csv_content)
    
    dataset = dataset_crud.create(
        db_session,
        organization_id=sample_organization.id,
        name="Test Dataset",
        description="Test evaluation dataset",
        source_type="csv",
        source_path=str(csv_path),
        num_examples=2
    )
    return dataset


@pytest.fixture(scope="function")
def sample_evaluation_run(db_session: Session, sample_prompt_template, sample_evaluation_dataset):
    """
    Create a sample evaluation run.
    
    Returns:
        EvaluationRun object with test metrics
    """
    from app.crud import evaluation_run as run_crud
    
    run = run_crud.create(
        db_session,
        prompt_template_id=sample_prompt_template.id,
        dataset_id=sample_evaluation_dataset.id,
        experiment_name="Test Run",
        num_examples=2,
        macro_pearson_r=0.85,
        macro_qwk=0.82,
        macro_plus_minus_one=0.95,
        per_dimension_metrics={
            "situation": {"pearson_r": 0.85, "qwk": 0.82, "plus_minus_one_accuracy": 0.95}
        },
        model_name="gpt-4o-mini",
        runtime_seconds=10.5
    )
    return run

