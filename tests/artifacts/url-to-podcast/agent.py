# agent.py

import os
from dotenv import load_dotenv
from any_agent import AgentConfig, AnyAgent
from any_agent.config import MCPStdio
from pydantic import BaseModel, Field
from fire import Fire

# ---- local / any-agent built-in tools ----
from tools.extract_text_from_url import extract_text_from_url
from tools.generate_podcast_script_with_llm import generate_podcast_script_with_llm

load_dotenv()

# ========== Structured output definition ==========
class StructuredOutput(BaseModel):
    url: str = Field(..., description="The original webpage URL supplied by the user.")
    num_hosts: int = Field(..., description="Number of podcast hosts / speakers requested.")
    script_text: str = Field(..., description="The full podcast script that was generated.")
    audio_file_path: str = Field(..., description="Filesystem path (inside ELEVENLABS_OUTPUT_DIR) or URL pointing to the generated multi-speaker podcast MP3 file.")


# ========== System (Multi-step) Instructions ==========
INSTRUCTIONS = """
You are an autonomous assistant that turns any public web article into a polished multi-speaker podcast in three clear stages.

Step-by-step workflow you MUST follow:
1. CONTENT EXTRACTION — Receive a URL from the user and call the `extract_text_from_url` tool to fetch and clean the main textual content of the page. If extraction fails, stop and return a helpful error.
2. SCRIPT WRITING — With the extracted text, invoke `generate_podcast_script_with_llm`, passing the user-requested number of hosts so the script alternates dialogue between distinct speakers (labelled **Host 1**, **Host 2**, etc.). Keep the script engaging, conversational and less than ~2,000 words.
3. AUDIO GENERATION — Send the entire finished script to the `generate_audio_script` tool from the ElevenLabs MCP server. A single call should return a high-quality MP3 that already contains all voices. Use the default voice mapping unless the user provides explicit voice IDs.

Upon completing these steps, respond ONLY with a JSON object that conforms exactly to the StructuredOutput schema (do NOT add any extra keys). Ensure `audio_file_path` is whatever location or URL the ElevenLabs server returns for the generated file.
"""

# ========== Tools definition ==========
TOOLS = [
    # local Python utility tools
    extract_text_from_url,
    generate_podcast_script_with_llm,
    # ElevenLabs MCP (text-to-speech)
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
            "ELEVENLABS_API_KEY": os.getenv("ELEVENLABS_API_KEY"),  # required
            # Optional overrides – read from environment if present
            "ELEVENLABS_VOICE_ID": os.getenv("ELEVENLABS_VOICE_ID", ""),
            "ELEVENLABS_MODEL_ID": os.getenv("ELEVENLABS_MODEL_ID", ""),
            "ELEVENLABS_OUTPUT_DIR": os.getenv("ELEVENLABS_OUTPUT_DIR", "output"),
        },
        # use the minimum necessary ElevenLabs tool
        tools=[
            "generate_audio_script",
        ],
    ),
]

# Build the agent
agent = AnyAgent.create(
    "openai",
    AgentConfig(
        model_id="o3",
        instructions=INSTRUCTIONS,
        tools=TOOLS,
        agent_args={"output_type": StructuredOutput},
        model_args={"tool_choice": "required"},
    ),
)


def run_agent(url: str, num_hosts: int = 2):
    """Create a multi-speaker podcast from the given webpage URL."""
    input_prompt = (
        f"Create an audio podcast with {num_hosts} hosts from this webpage: {url}\n"
        "Return only structured JSON per specification."
    )
    # pass num_hosts via prompt so the agent uses it when calling tools
    agent_trace = agent.run(prompt=input_prompt)

    # Persist the full execution trace for evaluation/debugging
    with open("generated_workflows/latest/agent_eval_trace.json", "w", encoding="utf-8") as f:
        f.write(agent_trace.model_dump_json(indent=2))

    return agent_trace.final_output


if __name__ == "__main__":
    Fire(run_agent)