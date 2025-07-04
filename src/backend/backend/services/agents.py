import shutil
import uuid

import dotenv
from loguru import logger

from backend.repositories.agents import AgentRepository
from backend.schemas import AgentConfig, AgentCreateRequest, AgentSummary
from backend.settings import settings
from backend.tasks import send_message_task
from backend.templates import USER_PROMPT
from backend.utils import download_agent_files

dotenv.load_dotenv()

BASE_URL = settings.A2A_AGENT_URL


class AgentService:
    def __init__(self, agent_repository: AgentRepository):
        self.agent_repository = agent_repository

    def _build_prompt(self, prompt: str) -> str:
        return USER_PROMPT.format(prompt)

    async def create_agent(self, request: AgentCreateRequest) -> AgentSummary:
        """Create a new agent with the provided prompt.

        This method receives a request to create a new agent. It builds the agent's prompt
        using the provided prompt from the request, saves the agent's metadata in the database,
        and creates a appends a new task to the Celery queue to send the message to the agent.

        The method immediately returns a summary of the created agent, which includes
        the agent's ID, summary, status, and creation timestamp.

        Args:
            request (AgentCreateRequest): The request containing the agent's prompt.

        Returns:
            AgentSummary: A summary of the created agent.
        """
        summary = request.prompt[:120] + "..." if len(request.prompt) > 120 else request.prompt
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
        """Retrieve the configuration of an agent by its ID.

        Args:
            agent_id (uuid.UUID): The unique identifier of the agent.

        Returns:
            AgentConfig: The configuration of the agent, including its summary, prompt,
            and availability of trace and download options.

        Raises:
            ValueError: If the agent with the specified ID does not exist.
        """
        record = self.agent_repository.get(agent_id)
        if not record:
            raise ValueError(f"Agent with ID {agent_id} not found.")

        response = AgentConfig(
            id=record.id,
            summary=record.summary,
            status=record.status,
            created_at=record.created_at,
            prompt=record.prompt,
            trace_available=record.trace_available,
            download_available=record.download_available,
        )

        return AgentConfig.model_validate(response)

    def get_agents(self) -> list[AgentSummary]:
        """Retrieve a list of all agents.

        Returns:
            list[AgentSummary]: A list of summaries for all agents, each containing
            the agent's ID, summary, status, and creation timestamp.
        """
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
        """Download the agent's directory as a zip file.

        This method retrieves the agent's directory based on its ID, compresses it into a zip file,
        and returns the path to the zip file.

        Args:
            agent_id (uuid.UUID): The unique identifier of the agent.

        Returns:
            str: The path to the zip file containing the agent's directory.

        Raises:
            ValueError: If the agent directory does not exist.
        """
        agent_dir = download_agent_files(agent_id)
        zip_path = shutil.make_archive(str(agent_dir), "zip", agent_dir)

        return zip_path
