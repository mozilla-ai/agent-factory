import uuid
from datetime import datetime
from pathlib import Path

import dotenv
import fire
from any_agent import AgentConfig, AgentFramework, AnyAgent
from any_agent.serving import A2AServingConfig
from any_agent.tools import search_tavily, visit_webpage

from agent_factory.instructions import INSTRUCTIONS
from agent_factory.tools import read_file, search_mcp_servers
from agent_factory.utils import build_run_instructions, save_agent_parsed_outputs, validate_agent_outputs

dotenv.load_dotenv()


def create_agent():
    framework = AgentFramework.TINYAGENT
    agent = AnyAgent.create(
        framework,
        AgentConfig(
            model_id="o3",
            instructions=INSTRUCTIONS,
            description="Agent for generating agentic workflows based on user prompts.",
            tools=[visit_webpage, search_tavily, search_mcp_servers, read_file],
            model_args={"tool_choice": "required"},  # Ensure tool choice is required
        ),
    )
    return agent


# def single_turn_generation(
#     user_prompt: str,
#     output_dir: Path | None = None,
# ):
#     """Generate python code for an agentic workflow based on the user prompt."""
#     if output_dir is None:
#         output_dir = Path.cwd()
#         uid = datetime.now().strftime("%Y-%m-%d_%H:%M:%S") + "_" + str(uuid.uuid4())[:8]
#         # store in a unique dir under generated_workflows by default
#         output_dir = output_dir / "generated_workflows" / uid
#     else:
#         # guarantee output_dir is PosixPath
#         output_dir = Path(output_dir)

#     output_dir.mkdir(parents=True, exist_ok=True)

#     agent = create_agent()

#     run_instructions = build_run_instructions(user_prompt)

#     agent_trace = agent.run(run_instructions, max_turns=30)

#     (output_dir / "agent_factory_trace.json").write_text(agent_trace.model_dump_json(indent=2))

#     (output_dir / "agent_factory_raw_output.txt").write_text(agent_trace.final_output)

#     agent_factory_outputs = validate_agent_outputs(agent_trace.final_output)
#     save_agent_parsed_outputs(agent_factory_outputs, output_dir)

#     print(f"Workflow files saved in: {output_dir}")


# def main():
#     fire.Fire(single_turn_generation)


def main():
    agent = create_agent()
    agent.serve(A2AServingConfig(port=5001, log_level="warning"))


if __name__ == "__main__":
    main()
