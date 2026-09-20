import os

import pytest

REQUIRED_ENV = {
    "ENVIRONMENT": "test",
    "LOG_LEVEL": "INFO",
    "GEMINI_API_KEY": "test-gemini-key",
    "TAVILY_API_KEY": "test-tavily-key",
    "NESTJS_API_URL": "http://localhost:3000",
    "REDIS_URL": "redis://localhost:6379/0",
}


def pytest_configure(config):
    for key, value in REQUIRED_ENV.items():
        os.environ.setdefault(key, value)


@pytest.fixture(scope="session")
def client():
    from fastapi.testclient import TestClient
    from app.main import app

    with TestClient(app) as test_client:
        yield test_client