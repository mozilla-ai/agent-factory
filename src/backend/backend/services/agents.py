import re
import shutil
import uuid
from pathlib import Path

import dotenv
from loguru import logger

from backend.repositories.agents import AgentRepository
from backend.schemas import AgentConfig, AgentCreateRequest, AgentSummary
from backend.settings import settings
from backend.tasks import send_message_task

dotenv.load_dotenv()

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

    def _update_agent_record(self, agent_id: uuid.UUID, **kwargs):
        logger.info(f"Updating agent record {agent_id} with {kwargs}")

    def _extract_code(self, code: str) -> str:
        match = re.search(r"```(?:python|markdown|toml)\n(.*)```$", code, re.DOTALL)
        if match:
            return match.group(1).strip()
        else:
            raise ValueError("Could not find a python code block in the provided string.")

    def _prepare_output_dir(self, agent_id: uuid.UUID) -> Path:
        output_dir = Path.cwd()
        output_dir = output_dir / "generated_agents" / str(agent_id)
        output_dir.mkdir(parents=True, exist_ok=True)
        return output_dir

    def _save_agent(self, agent_id, python: str, readme: str, pyproject: str):
        output_dir = self._prepare_output_dir(agent_id)
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

    def _update_agent_status(self, agent_id: uuid.UUID, status: str):
        logger.info(f"Updating agent {agent_id} status to {status}")
        self.agent_repository.update(agent_id, status=status)

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
            send_message_task.delay(prompt, agent_id=str(record.id))
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

    def download_agent(self, agent_id: uuid.UUID) -> str:
        agent_dir = self._prepare_output_dir(agent_id)

        if not agent_dir.exists():
            raise ValueError(f"Agent directory for {agent_id} not found.")

        zip_path = Path.cwd() / f"{agent_id}.zip"

        # Create the zip file from the agent directory
        shutil.make_archive(
            base_name=str(zip_path).rstrip(".zip"), format="zip", root_dir=agent_dir.parent, base_dir=agent_dir.name
        )

        return str(zip_path)
