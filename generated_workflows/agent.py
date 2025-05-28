import os

from any_agent import AgentConfig, AnyAgent
from any_agent.config import MCPStdio
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from tools.generate_podcast_script_with_llm import generate_podcast_script_with_llm
from tools.translate_text_with_llm import translate_text_with_llm

# Load environment variables
load_dotenv()


# Define structured output
class PodcastScriptWorkflowOutput(BaseModel):
    spanish_podcast_script: str = Field(..., description="The final podcast script in Spanish.")
    output_file_path: str = Field(..., description="The relative file path of the saved script.")


INSTRUCTIONS = (
    "You are an agent that generates a podcast script in Spanish given a user topic.\n"
    "Follow these steps:\n"
    "1. Take the user's topic and generate a podcast script in English using the generate_podcast_script_with_llm tool (use 2 hosts).\n"
    "2. Translate the generated English podcast script to Spanish using the translate_text_with_llm tool (source_language='English', target_language='Spanish').\n"
    "3. Save ONLY the Spanish podcast script to a .txt file in the 'generated_workflows/' directory with the filename format 'podcast_script_[safe_topic].txt', where [safe_topic] is the user topic lowercased, spaces replaced with underscores, and non-alphanumeric characters removed except underscores or hyphens. Use the filesystem MCP's 'write_file' tool for saving.\n"
    "4. As final output, return the Spanish script and the relative file path to the saved .txt file using the provided output schema."
)

# Filesystem MCP configuration
cwd = os.getcwd()
mcp_filesystem = MCPStdio(
    command="docker",
    args=[
        "run",
        "-i",
        "--rm",
        "--mount",
        f"type=bind,src={cwd}/generated_workflows,dst=/projects/generated_workflows",
        "mcp/filesystem",
        "/projects",
    ],
    # Only using write_file tool for this workflow
    tools=["write_file"],
)

agent = AnyAgent.create(
    "openai",
    AgentConfig(
        model_id="gpt-4.1",
        instructions=INSTRUCTIONS,
        tools=[
            generate_podcast_script_with_llm,
            translate_text_with_llm,
            mcp_filesystem,
        ],
        agent_args={"output_type": PodcastScriptWorkflowOutput},
    ),
)

if __name__ == "__main__":
    user_topic = input("Enter the topic for the podcast (in English or Spanish): ")
    prompt = f"Generate a Spanish podcast script for the topic: '{user_topic}'. Follow the workflow and save script as a .txt file."
    agent_trace = agent.run(prompt=prompt)

    with open("generated_workflows/agent_trace.json", "w", encoding="utf-8") as f:
        f.write(agent_trace.model_dump_json(indent=2))
