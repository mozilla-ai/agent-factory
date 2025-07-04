import asyncio
import io
import json
import uuid
from pathlib import Path

import httpx
from a2a.types import JSONRPCErrorResponse, SendMessageSuccessResponse
from loguru import logger

from backend.celery_app import celery_app
from backend.client import AgentClient
from backend.db import session_manager
from backend.repositories.agents import AgentRepository
from backend.schemas import AgentStatus
from backend.settings import settings
from backend.storage import storage_client
from backend.templates import AGENT_CODE_TEMPLATE, DOCKERFILE_TEMPLATE

BASE_URL = settings.A2A_AGENT_URL


def _get_agent_repository():
    with session_manager.session() as session:
        yield AgentRepository(session)


def _update_agent_status(agent_id: uuid.UUID, status: str):
    logger.info(f"Updating agent {agent_id} status to {status}")
    for repo in _get_agent_repository():
        repo.update(agent_id, status=status)


def _save_agent(result: dict[str, str], agent_id: uuid.UUID) -> None:
    bucket_name = settings.S3_BUCKET_NAME
    try:
        storage_client.head_bucket(Bucket=bucket_name)
    except Exception:
        storage_client.create_bucket(Bucket=bucket_name)

    try:
        agent_code = AGENT_CODE_TEMPLATE.format(**result)
        storage_client.put_object(
            Bucket=bucket_name,
            Key=f"{agent_id}/agent.py",
            Body=io.BytesIO(agent_code.encode()),
            ContentType="text/x-python",
        )

        storage_client.put_object(
            Bucket=bucket_name,
            Key=f"{agent_id}/INSTRUCTIONS.md",
            Body=io.BytesIO(result["run_instructions"].encode()),
            ContentType="text/markdown",
        )

        storage_client.put_object(
            Bucket=bucket_name,
            Key=f"{agent_id}/requirements.txt",
            Body=io.BytesIO(result["dependencies"].encode()),
            ContentType="text/plain",
        )

        storage_client.put_object(
            Bucket=bucket_name,
            Key=f"{agent_id}/Dockerfile",
            Body=io.BytesIO(DOCKERFILE_TEMPLATE.encode()),
            ContentType="text/plain",
        )

        tools_dir = Path("backend/tools")
        for tool_file in tools_dir.iterdir():
            if tool_file.is_file() and (tool_file.stem in agent_code or tool_file.name == "__init__.py"):
                storage_client.upload_file(
                    str(tool_file),
                    bucket_name,
                    f"{agent_id}/tools/{tool_file.name}",
                )

        logger.info(f"Agent files saved to bucket {bucket_name}")

    except Exception as e:
        logger.error(f"Warning: Failed to parse and save agent outputs: {str(e)}")


async def _send_message_async(prompt: str, agent_id: uuid.UUID):
    async with httpx.AsyncClient() as httpx_client:
        agent = AgentClient(base_url=BASE_URL, httpx_client=httpx_client)
        try:
            response = await agent.send_message(prompt, timeout=600)
            if response:
                if isinstance(response.root, JSONRPCErrorResponse):
                    raise ValueError(f"Error from agent: {response.error.message}")
                if isinstance(response.root, SendMessageSuccessResponse):
                    result = json.loads(response.root.result.status.message.parts[0].root.text)
                    _save_agent(result, agent_id)
        except httpx.RequestError as e:
            logger.error(f"Request error: {e}")


@celery_app.task
def send_message_task(prompt: str, agent_id: str):
    """Sends a message to the agent and updates its status.

    This fuctions runs as a Celery task. Whenever a new task is submitted to the queue,
    a Celery worker will pick it up and execute this function.

    Args:
        prompt (str): The message to send to the agent.
        agent_id (str): The UUID of the agent to send the message to.

    Raises:
        Exception: If there is an error communicating with the agent.
    """
    agent_uuid = uuid.UUID(agent_id)
    _update_agent_status(agent_id=agent_uuid, status=AgentStatus.PROCESSING)
    try:
        asyncio.run(_send_message_async(prompt, agent_uuid))
        _update_agent_status(agent_id=agent_uuid, status=AgentStatus.COMPLETED)
    except Exception as e:
        _update_agent_status(agent_id=agent_uuid, status=AgentStatus.FAILED)
        logger.info(f"Error communicating with agent: {e}")
