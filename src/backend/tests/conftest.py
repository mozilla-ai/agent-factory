from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from backend.api.deps import get_agent_service
from backend.main import app
from backend.repositories.agents import AgentRepository
from backend.services.agents import AgentService


@pytest.fixture
def mock_agent_service():
    service = MagicMock(spec=AgentService)
    service.create_agent = AsyncMock()
    return service


@pytest.fixture
def mock_agent_repository():
    return MagicMock(spec=AgentRepository)


@pytest.fixture
def client(mock_agent_service: MagicMock):
    app.dependency_overrides[get_agent_service] = lambda: mock_agent_service
    yield TestClient(app)
    app.dependency_overrides = {}


# Mock the Celery task
@pytest.fixture
def mock_send_message_task(mocker):
    return mocker.patch("backend.tasks.send_message_task.delay", return_value=None)
