"""Pytest configuration and shared fixtures."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient
from unittest.mock import MagicMock

from app.db.base import Base, get_db
from app.main import app
from app.models import response, agent_prompt, response_validation


@pytest.fixture(scope="function")
def db_engine():
    """Create an in-memory SQLite engine for testing."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session(db_engine):
    """Create a new database session for a test."""
    TestingSessionLocal = sessionmaker(
        autocommit=False, autoflush=False, bind=db_engine
    )
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client with database session override."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def mock_anthropic_client():
    """Create a mock Anthropic client."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text='[{"company_name": "Test Corp", "address": "123 Main St, City, ST 12345"}]')]
    mock_response.stop_reason = "end_turn"
    mock_client.messages.create.return_value = mock_response
    return mock_client


@pytest.fixture
def sample_companies():
    """Sample company data for testing."""
    return [
        {
            "company_name": "Acme Corporation",
            "address": "123 Main Street, Springfield, IL 62701",
            "source_url": "https://example.com/page1"
        },
        {
            "company_name": "Tech Solutions Inc",
            "address": "456 Oak Avenue, Austin, TX 78701",
            "source_url": "https://example.com/page2"
        },
        {
            "company_name": "Global Widgets",
            "address": "789 Pine Road, Seattle, WA 98101",
            "source_url": "https://example.com/page3"
        }
    ]


@pytest.fixture
def sample_incomplete_addresses():
    """Sample companies with incomplete addresses for validation testing."""
    return [
        {
            "company_name": "Complete Co",
            "address": "123 Main St, Austin, TX 78701"
        },
        {
            "company_name": "Missing Zip",
            "address": "456 Oak Ave, Seattle, WA"
        },
        {
            "company_name": "Street Only",
            "address": "789 Pine Rd"
        },
        {
            "company_name": "No Address",
            "address": ""
        }
    ]
