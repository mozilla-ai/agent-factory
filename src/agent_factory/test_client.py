import json
from pathlib import Path
from typing import Any
from uuid import uuid4

import fire
import httpx
from a2a.client import A2ACardResolver, A2AClient
from a2a.types import (
    AgentCard,
    MessageSendParams,
    SendMessageRequest,
)

from agent_factory.instructions import AGENT_CODE_TEMPLATE, AGENT_CODE_TEMPLATE_RUN
from agent_factory.utils import clean_python_code_with_autoflake, logger, setup_output_directory

PUBLIC_AGENT_CARD_PATH = "/.well-known/agent.json"
EXTENDED_AGENT_CARD_PATH = "/agent/authenticatedExtendedCard"


def save_agent_outputs(result: dict[str, str], output_dir: Path) -> None:
    """Save the agent outputs to files.

    This function takes a dictionary containing the agent outputs and saves them to
    an output directory. It creates three different files in the output directory:
        - agent.py: Contains the agent code.
        - README.md: Contains the run instructions in Markdown format.
        - requirements.txt: Contains the dependencies line by line.

    Args:
        result: A dictionary containing the agent outputs. It should include the following keys:
            - agent_code: The Python code for the agent.
            - readme: The instructions for running the agent in Markdown format.
            - dependencies: A string containing the dependencies required by the agent, one per line.

    Raises:
        Exception: If there is an error while writing the files to the output directory.
    """
    try:
        agent_path = output_dir / "agent.py"
        readme_path = output_dir / "README.md"
        requirements_path = output_dir / "requirements.txt"
        tools_dir_path = output_dir / "tools"
        tools_dir_path.mkdir(exist_ok=True)
        agent_code = f"{AGENT_CODE_TEMPLATE.format(**result)} \n{AGENT_CODE_TEMPLATE_RUN.format(**result)}"

        clean_agent_code = clean_python_code_with_autoflake(agent_code)

        with agent_path.open("w", encoding="utf-8") as f:
            f.write(clean_agent_code)

        with readme_path.open("w", encoding="utf-8") as f:
            f.write(result["readme"])

        with requirements_path.open("w", encoding="utf-8") as f:
            f.write(result["dependencies"])

        tools_dir = Path("src/agent_factory/tools")
        for tool_file in tools_dir.iterdir():
            if tool_file.is_file() and (tool_file.stem in agent_code or tool_file.name == "__init__.py"):
                tool_destination = tools_dir_path / tool_file.name
                # Copy the tool file to the output directory
                tool_destination.write_text(tool_file.read_text(encoding="utf-8"), encoding="utf-8")

        logger.info(f"Agent files saved to {output_dir}")

    except Exception as e:
        logger.warning(f"Warning: Failed to parse and save agent outputs: {str(e)}")


async def generate(
    message: str,
    output_dir: Path | None = None,
    host: str = "localhost",
    port: int = 8080,
    timeout: int = 600,
) -> None:
    """Main entry point for the A2A client application.

    Args:
        message (str): The message to send to the agent.
        host (str): The host address for the agent server (default: "localhost").
        port (int): The port for the agent server (default: 8080).
        timeout (str): The timeout for the request in seconds (default: 600).
    """
    base_url = f"http://{host}:{port}"

    async with httpx.AsyncClient() as httpx_client:
        resolver = A2ACardResolver(
            httpx_client=httpx_client,
            base_url=base_url,
        )

        try:
            agent_card: AgentCard = await resolver.get_agent_card()
        except Exception as e:
            logger.error(f"Critical error fetching public agent card: {e}", exc_info=True)
            raise RuntimeError("Failed to fetch the public agent card. Cannot continue.") from e

        client = A2AClient(httpx_client=httpx_client, agent_card=agent_card)
        logger.info("A2AClient initialized.")

        send_message_payload: dict[str, Any] = {
            "message": {
                "role": "user",
                "parts": [{"kind": "text", "text": message}],
                "messageId": uuid4().hex,
            },
        }
        request = SendMessageRequest(id=str(uuid4()), params=MessageSendParams(**send_message_payload))

        response = await client.send_message(request, http_kwargs={"timeout": timeout})
        logger.info(response.model_dump(mode="json", exclude_none=True))

        result = json.loads(response.root.result.status.message.parts[0].root.text)
        logger.info(f"Received response from agent: {result}")

        output_dir = setup_output_directory(output_dir)
        save_agent_outputs(result, output_dir)


def main():
    fire.Fire(generate)


if __name__ == "__main__":
    fire.Fire(main)
