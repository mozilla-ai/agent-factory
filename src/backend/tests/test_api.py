import uuid
from datetime import datetime
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from backend.schemas import AgentConfig, AgentCreateRequest, AgentStatus, AgentSummary


@pytest.mark.asyncio
async def test_create_agent_endpoint(client: TestClient, mock_agent_service: MagicMock):
    # Arrange
    request_data = {"prompt": "Create a new agent test"}
    agent_id = uuid.uuid4()
    mock_agent_service.create_agent.return_value = AgentSummary(
        id=agent_id,
        summary="Create a new agent test",
        status=AgentStatus.COMPLETED,
        created_at=datetime.now(),
    )

    # Act
    response = client.post("/api/v1/agents/", json=request_data)

    # Assert
    assert response.status_code == 201
    mock_agent_service.create_agent.assert_called_once_with(AgentCreateRequest(prompt="Create a new agent test"))
    assert response.json()["id"] == str(agent_id)
    assert response.json()["summary"] == "Create a new agent test"
    assert response.json()["status"] == AgentStatus.COMPLETED.value


def test_get_agents_endpoint(client: TestClient, mock_agent_service: MagicMock):
    # Arrange
    agent_id = uuid.uuid4()
    mock_agent_service.get_agents.return_value = [
        AgentSummary(
            id=agent_id,
            summary="Get agents test",
            status=AgentStatus.COMPLETED,
            created_at=datetime.now(),
        )
    ]

    # Act
    response = client.get("/api/v1/agents/")

    # Assert
    assert response.status_code == 200
    mock_agent_service.get_agents.assert_called_once()
    assert len(response.json()) == 1
    assert response.json()[0]["id"] == str(agent_id)
    assert response.json()[0]["summary"] == "Get agents test"
    assert response.json()[0]["status"] == AgentStatus.COMPLETED.value


def test_get_agent_endpoint(client: TestClient, mock_agent_service: MagicMock):
    # Arrange
    agent_id = uuid.uuid4()
    mock_agent_service.get_agent.return_value = AgentConfig(
        id=agent_id,
        summary="Get agent test",
        status=AgentStatus.COMPLETED,
        created_at=datetime.now(),
        prompt="Get agent test",
        trace_available=False,
        download_available=False,
    )

    # Act
    response = client.get(f"/api/v1/agents/{agent_id}")

    # Assert
    assert response.status_code == 200
    mock_agent_service.get_agent.assert_called_once_with(agent_id)
    assert response.json()["id"] == str(agent_id)
    assert response.json()["summary"] == "Get agent test"
    assert response.json()["status"] == AgentStatus.COMPLETED.value
    assert response.json()["prompt"] == "Get agent test"
    assert response.json()["trace_available"] is False
    assert response.json()["download_available"] is False
