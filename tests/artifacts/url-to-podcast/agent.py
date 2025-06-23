# agent.py

import os
from dotenv import load_dotenv
from any_agent import AgentConfig, AnyAgent, AgentRunError
from any_agent.config import MCPStdio
from pydantic import BaseModel, Field
from fire import Fire

# ------------- Local (callable) tools -------------
from tools.extract_text_from_url import extract_text_from_url
from tools.generate_podcast_script_with_llm import generate_podcast_script_with_llm

# ------------- Load env vars -------------
load_dotenv()

# ========== Structured output definition ==========
class StructuredOutput(BaseModel):
    url: str = Field(..., description="Original webpage URL that inspired the podcast")
    script_text: str = Field(..., description="Full podcast script that was generated for multiple speakers")
    audio_file_path: str = Field(..., description="Filesystem path (or URL) to the final generated MP3 podcast audio")

# ========== System (Multi-step) Instructions ==========
INSTRUCTIONS = """
You are an autonomous podcast-production agent that must follow this 4-step workflow and use the provided tools only:
STEP 1 ― Fetch & Extract
    • Use extract_text_from_url(url) to pull all readable text from the user-supplied webpage.
    • If extraction fails or the content is empty, stop and raise an error.
STEP 2 ― Draft Script
    • Summarise or reorganise the extracted text into an engaging podcast script.
    • Call generate_podcast_script_with_llm(document_text, num_hosts=n) where n is provided by the user (default 2).
    • Make sure each speaker turn is clearly labelled (e.g. "Host 1:", "Host 2:").
STEP 3 ― Text-to-Speech
    • Send the entire script text to the ElevenLabs MCP tool generate_audio_script.
    • Provide it the raw script (plain text). Let the server choose voices automatically unless the user supplies voice IDs.
    • The tool returns a path/URL to a single MP3 file that contains all speakers.
STEP 4 ― Respond
    • Return a JSON object that matches the StructuredOutput schema (url, script_text, audio_file_path).
    • Do not include anything else in the final answer.
General Rules:
    • ALWAYS call tools; never attempt tasks manually when a tool exists.
    • Keep conversations concise and use no more than 15 total tool calls.
    • Reply ONLY with valid JSON matching the output schema.
"""

# ========== Tools definition ===========
TOOLS = [
    extract_text_from_url,
    generate_podcast_script_with_llm,
    # ElevenLabs Text-to-Speech MCP server (Docker installation variant)
    MCPStdio(
        command="docker",
        args=[
            "run",
            "-i",
            "--rm",
            "-e",
            "ELEVENLABS_API_KEY",
            "mcp/elevenlabs",
        ],
        env={
            "ELEVENLABS_API_KEY": os.getenv("ELEVENLABS_API_KEY"),
        },
        tools=[
            "generate_audio_script",  # only tool we need for this workflow
        ],
    ),
]

# ========== Create the agent ===========
agent = AnyAgent.create(
    "openai",
    AgentConfig(
        model_id="o3",
        instructions=INSTRUCTIONS,
        tools=TOOLS,
        output_type=StructuredOutput,
        model_args={"tool_choice": "required"},
    ),
)

# ========== CLI entrypoint =============

def run_agent(url: str, num_hosts: int = 2):
    """Generate a multi-speaker podcast (audio + script) from a webpage URL."""
    # Compose prompt — the agent will break tasks into steps internally
    prompt_template = (
        "Create an engaging {num_hosts}-speaker audio podcast based on the content of this webpage: {url}\n"
        "Return the final result following the steps in your system instructions."
    )
    input_prompt = prompt_template.format(url=url, num_hosts=num_hosts)

    try:
        agent_trace = agent.run(prompt=input_prompt, max_turns=20)
    except AgentRunError as e:
        agent_trace = e.trace
        print(f"Agent execution failed: {e}")
        print("Partial trace retrieved …")

    # Persist the trace for evaluation/inspection
    os.makedirs("generated_workflows/latest", exist_ok=True)
    with open("generated_workflows/latest/agent_eval_trace.json", "w", encoding="utf-8") as f:
        f.write(agent_trace.model_dump_json(indent=2))

    return agent_trace.final_output


if __name__ == "__main__":
    Fire(run_agent)