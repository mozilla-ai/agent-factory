import uuid
from datetime import datetime
from unittest.mock import MagicMock

import pytest

from backend.records.agents import AgentRecord
from backend.schemas import AgentCreateRequest, AgentStatus, AgentSummary
from backend.services.agents import AgentService


@pytest.mark.asyncio
async def test_create_agent_service_sends_celery_task(
    mock_agent_repository: MagicMock, mock_send_message_task: MagicMock
):
    agent_service = AgentService(mock_agent_repository)
    request = AgentCreateRequest(prompt="Create a new agent")

    mock_agent_repository.create.return_value = AgentSummary(
        id=uuid.uuid4(),
        summary="Create a new agent...",
        status=AgentStatus.PENDING,
        created_at=datetime.now(),
    )

    agent_summary = await agent_service.create_agent(request)

    mock_send_message_task.assert_called_once_with(
        agent_service._build_prompt(request.prompt), agent_id=str(agent_summary.id)
    )
    assert agent_summary.summary == "Create a new agent..."
    assert agent_summary.status == AgentStatus.PENDING
    mock_agent_repository.create.assert_called_once()


def test_get_agent_service(mock_agent_repository: MagicMock):
    agent_id = uuid.uuid4()
    agent_service = AgentService(mock_agent_repository)

    mock_agent_repository.get.return_value = MagicMock(
        id=agent_id,
        summary="Test Summary",
        status=AgentStatus.COMPLETED,
        prompt="Test Prompt",
        trace_available=True,
        download_available=True,
        created_at=datetime.now(),
    )

    agent_config = agent_service.get_agent(agent_id)

    assert agent_config.id == agent_id
    assert agent_config.prompt == "Test Prompt"
    mock_agent_repository.get.assert_called_once_with(agent_id)


def test_get_agents_service(mock_agent_repository):
    agent_service = AgentService(mock_agent_repository)

    mock_agent_repository.list.return_value = [
        AgentRecord(
            id=uuid.uuid4(),
            summary="Test Summary 1",
            prompt="Test Prompt 1",
            trace_available=True,
            download_available=False,
            status=AgentStatus.FAILED,
            created_at=datetime.now(),
        ),
        AgentRecord(
            id=uuid.uuid4(),
            summary="Test Summary 2",
            status=AgentStatus.PENDING,
            prompt="Test Prompt 2",
            trace_available=False,
            download_available=False,
            created_at=datetime.now(),
        ),
    ]

    agents = agent_service.get_agents()

    assert len(agents) == 2
    assert agents[0].summary == "Test Summary 1"
    mock_agent_repository.list.assert_called_once()
