# agent.py

import os
from dotenv import load_dotenv
from any_agent import AgentConfig, AnyAgent
from any_agent.config import MCPStdio
from pydantic import BaseModel, Field
from fire import Fire

# ---- Local tools ------------------------------------------------------------
from tools.extract_text_from_url import extract_text_from_url
from tools.generate_podcast_script_with_llm import generate_podcast_script_with_llm

load_dotenv()

# ================= Structured output =========================================
class StructuredOutput(BaseModel):
    url: str = Field(..., description="The original URL that was processed.")
    num_hosts: int = Field(..., description="Number of hosts/speakers requested for the podcast script.")
    podcast_script: str = Field(..., description="The generated multi-speaker podcast script.")
    audio_file_path: str = Field(..., description="Filesystem path (or URL) of the generated final podcast audio file.")


# ================= System (multi-step) instructions ==========================
INSTRUCTIONS = """
You are a podcast-production assistant.  Follow this strictly ordered workflow:

1. INPUT  →  Receive a web URL (web_url) and an integer (num_hosts) that tells you how many distinct hosts/speakers the final podcast must feature (minimum 2, default 2).

2. EXTRACT →  Call the extract_text_from_url tool to pull the primary textual content from the provided URL.  If extraction fails, halt and return an error message in podcast_script.

3. SCRIPT  →  Feed the extracted text into generate_podcast_script_with_llm, passing num_hosts so the script contains exactly that many clearly labelled speakers (e.g. "Host 1:", "Host 2:").  The script must include an intro and an outro.

4. AUDIO   →  Pass the full script to the generate_audio_script tool (from the ElevenLabs MCP server).  Supply the script as a **plain string**; the server will automatically create distinct voices based on the speaker labels.  Capture the returned audio job ID or path, then call get_audio_file to download the final MP3.  Save the file path returned by get_audio_file.

5. OUTPUT  →  Return a JSON object of type StructuredOutput containing:
     • url
     • num_hosts
     • podcast_script
     • audio_file_path  (absolute or relative path to the MP3)

General rules:
• Always use the tools exactly as described.
• Do NOT add extra commentary outside the StructuredOutput schema.
• If any step fails, populate podcast_script with a clear error description and leave audio_file_path empty.
"""

# ================= MCP (ElevenLabs) setup ====================================
elevenlabs_mcp = MCPStdio(
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
        "generate_audio_script",  # turn full script with multiple speakers into audio
        "get_audio_file",         # download the final MP3 file
    ],
)

TOOLS = [
    extract_text_from_url,
    generate_podcast_script_with_llm,
    elevenlabs_mcp,
]

# ================= Agent creation ============================================
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


# ================= CLI wrapper ===============================================

def run_agent(web_url: str, num_hosts: int = 2):
    """Generate a multi-speaker podcast from a web page."""
    input_prompt = (
        f"Please create an audio podcast with {num_hosts} hosts based on the contents of: {web_url}"
    )
    agent_trace = agent.run(prompt=input_prompt)

    # Save full trace for evaluation
    os.makedirs("generated_workflows/latest", exist_ok=True)
    with open("generated_workflows/latest/agent_eval_trace.json", "w", encoding="utf-8") as f:
        f.write(agent_trace.model_dump_json(indent=2))

    return agent_trace.final_output


if __name__ == "__main__":
    Fire(run_agent)
