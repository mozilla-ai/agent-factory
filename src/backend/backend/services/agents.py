import asyncio
import json
import re
from pathlib import Path
from uuid import UUID

import httpx
from loguru import logger

from backend.client import AgentClient
from backend.repositories.agents import AgentRepository
from backend.schemas import AgentConfig, AgentCreateRequest, AgentStatus, AgentSummary
from backend.settings import settings

BASE_URL = settings.A2A_AGENT_URL

USER_PROMPT = """Generate Python code for an agentic workflow using the `any-agent` library
to do the following:
{0}

Use appropriate tools in the agent configuration:
- Select relevant tools from `tools/available_tools.md`.
- Use the `search_mcp_servers` tool to discover and add MCP servers that provide relevant tools
    to the configuration.

Always use the simplest and most efficient tools available for the task.
"""


class AgentService:
    def __init__(self, agent_repository: AgentRepository):
        self.agent_repository = agent_repository

    def _build_prompt(self, prompt: str) -> str:
        return USER_PROMPT.format(prompt)

    def _update_agent_record(self, agent_id: UUID, **kwargs):
        logger.info(f"Updating agent record {agent_id} with {kwargs}")

    def _extract_and_save_code(self, python_string: str):
        output_dir = Path.cwd()
        result_path = output_dir / "agent.py"
        logger.info(f"Saving agent code to {result_path}")

        match = re.search(r"```python\n(.*)```", python_string, re.DOTALL)
        if match:
            python_code = match.group(1)
            try:
                result_path.write_text(python_code)
                logger.info(f"Successfully extracted the code and wrote it to '{result_path}'")
            except OSError as e:
                print(f"Error writing to file: {e}")
        else:
            print("Could not find a python code block in the provided string.")

    def _update_agent_status(self, agent_id: UUID, status: str):
        logger.info(f"Updating agent {agent_id} status to {status}")
        self.agent_repository.update(agent_id, status=status)

    async def _send_message(self, prompt: str, agent_id: UUID):
        self._update_agent_status(agent_id=agent_id, status=AgentStatus.PROCESSING)
        async with httpx.AsyncClient() as httpx_client:
            agent = AgentClient(base_url=BASE_URL, httpx_client=httpx_client)
            try:
                response = await agent.send_message(prompt, timeout=600)
                if response:
                    self._update_agent_status(agent_id=agent_id, status=AgentStatus.COMPLETED)
                    result = json.loads(response.root.result.status.message.parts[0].root.text)
                    python_string = result["result"]
                    self._extract_and_save_code(python_string)

            except Exception as e:
                self._update_agent_status(agent_id=agent_id, status=AgentStatus.FAILED)
                logger.info(f"Error communicating with agent: {e}")

    async def create_agent(self, request: AgentCreateRequest) -> AgentSummary:
        # TODO: Implement the logic to create a summary for the agent.
        summary = request.prompt[:120]
        prompt = self._build_prompt(request.prompt)

        record = self.agent_repository.create(
            summary=summary,
            prompt=prompt,
            trace_available=False,
            download_available=False,
        )

        try:
            asyncio.create_task(self._send_message(prompt, agent_id=record.id))
        except Exception as e:
            logger.error(f"Failed to send message to agent: {e}")

        response = AgentSummary(
            id=record.id,
            summary=record.summary,
            status=record.status,
            created_at=record.created_at,
        )

        return AgentSummary.model_validate(response)

    def get_agent(self, agent_id: uuid.UUID) -> AgentConfig:
        record = self.agent_repository.get(agent_id)
        if not record:
            raise ValueError(f"Agent with ID {agent_id} not found.")

        summary = AgentSummary(
            id=record.id,
            summary=record.summary,
            status=record.status,
            created_at=record.created_at,
        )

        response = AgentConfig(
            summary=summary,
            prompt=record.prompt,
            trace_available=record.trace_available,
            download_available=record.download_available,
        )

        return AgentConfig.model_validate(response)

    def get_agents(self) -> list[AgentSummary]:
        records = self.agent_repository.list()
        response = [
            AgentSummary(
                id=record.id,
                summary=record.summary,
                status=record.status,
                created_at=record.created_at,
            )
            for record in records
        ]

        return [AgentSummary.model_validate(agent) for agent in response]

    def download_agent(self, agent_id: UUID):
        # TODO: Implement the logic to download the agent.
        pass
