"""
Pytest configuration and fixtures.
"""

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.config.settings import Settings, get_settings


@pytest.fixture
def test_settings():
    """Test settings fixture."""
    return Settings(
        DEBUG=True,
        LOG_LEVEL="DEBUG",
        DB_HOST="localhost",
        DB_NAME="test_ops_assistant",
        VECTOR_STORE_TYPE="chroma",
        CHROMA_COLLECTION="test_ops_knowledge",
    )


@pytest.fixture
def client(test_settings):
    """Test client fixture."""
    def get_test_settings():
        return test_settings

    app.dependency_overrides[get_settings] = get_test_settings

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()


@pytest.fixture
def sample_document():
    """Sample document fixture."""
    return {
        "filename": "test.txt",
        "content": "This is a test document about MySQL troubleshooting.",
        "metadata": {
            "department": "ops",
            "service": "mysql",
            "level": "P1",
        },
    }


@pytest.fixture
def sample_chunks():
    """Sample chunks fixture."""
    return [
        {
            "content": "MySQL connection error can be caused by various factors.",
            "metadata": {
                "chunk_index": 0,
                "page_number": 1,
            },
        },
        {
            "content": "Check if MySQL service is running: systemctl status mysql",
            "metadata": {
                "chunk_index": 1,
                "page_number": 1,
            },
        },
    ]


@pytest.fixture
def sample_chat_history():
    """Sample chat history fixture."""
    return [
        {"role": "user", "content": "MySQL connection failed"},
        {"role": "assistant", "content": "Please check if MySQL service is running."},
    ]
