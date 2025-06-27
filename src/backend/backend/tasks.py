import asyncio
import json
import re
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
from backend.utils import create_agent_file

BASE_URL = settings.A2A_AGENT_URL


def _get_agent_repository():
    with session_manager.session() as session:
        yield AgentRepository(session)


def _update_agent_status(agent_id: uuid.UUID, status: str):
    logger.info(f"Updating agent {agent_id} status to {status}")
    for repo in _get_agent_repository():
        repo.update(agent_id, status=status)


def _extract_code(code: str) -> str:
    match = re.search(r"```(?:python|markdown|toml)\n(.*)```$", code, re.DOTALL)
    if match:
        return match.group(1).strip()
    else:
        raise ValueError("Could not find a python code block in the provided string.")


def _prepare_output_dir(agent_id: uuid.UUID) -> Path:
    output_dir = Path.cwd()
    output_dir = output_dir / "generated_agents" / str(agent_id)
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def _save_agent(agent_id, python: str, readme: str, pyproject: str):
    output_dir = _prepare_output_dir(agent_id)
    python_path = output_dir / "agent.py"
    readme_path = output_dir / "README.md"
    pyproject_path = output_dir / "pyproject.toml"
    logger.info(f"Saving agent code to {output_dir}")

    try:
        python_path.write_text(python)
        readme_path.write_text(readme)
        pyproject_path.write_text(pyproject)
        logger.info(f"Successfully extracted the code and wrote it to '{output_dir}'")
    except OSError as e:
        logger.error(f"Error writing to file: {e}")
        raise


async def _send_message_async(prompt: str, agent_id: uuid.UUID):
    async with httpx.AsyncClient() as httpx_client:
        agent = AgentClient(base_url=BASE_URL, httpx_client=httpx_client)
        response = await agent.send_message(prompt, timeout=600)
        if response:
            if isinstance(response.root, JSONRPCErrorResponse):
                logger.error(f"Error from agent: {response.error.message}")
                _update_agent_status(agent_id=agent_id, status=AgentStatus.FAILED)
                return
            if isinstance(response.root, SendMessageSuccessResponse):
                _update_agent_status(agent_id=agent_id, status=AgentStatus.COMPLETED)
                result = json.loads(response.root.result.status.message.parts[0].root.text)
                python_string = result["result"]

                python_code = _extract_code(python_string)
                readme_code = _extract_code(create_agent_file("readme", python_code))
                pyproject_code = _extract_code(create_agent_file("toml", python_code))

                _save_agent(agent_id, python_code, readme_code, pyproject_code)


@celery_app.task
def send_message_task(prompt: str, agent_id: str):
    agent_uuid = uuid.UUID(agent_id)
    _update_agent_status(agent_id=agent_uuid, status=AgentStatus.PROCESSING)
    try:
        asyncio.run(_send_message_async(prompt, agent_uuid))
    except Exception as e:
        _update_agent_status(agent_id=agent_uuid, status=AgentStatus.FAILED)
        logger.info(f"Error communicating with agent: {e}")
