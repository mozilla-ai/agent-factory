# agent.py

import os
from dotenv import load_dotenv
from any_agent import AgentConfig, AnyAgent, AgentRunError
from any_agent.config import MCPStdio
from pydantic import BaseModel, Field
from fire import Fire

# ---- Local tool imports ----
from tools.extract_text_from_url import extract_text_from_url
from tools.generate_podcast_script_with_llm import generate_podcast_script_with_llm

# Load .env file
load_dotenv()

# ========== Structured output definition ==========
class PodcastOutput(BaseModel):
    url: str = Field(..., description="Original webpage URL supplied by the user.")
    extracted_text: str = Field(..., description="Plain text extracted from the webpage, trimmed if very long.")
    podcast_script: str = Field(..., description="Dialogue-style podcast script with multiple speakers.")
    audio_file_path: str = Field(..., description="Filesystem path (or URL) to the final combined podcast audio file.")

# ========== System (Multi-step) Instructions ==========
INSTRUCTIONS = """
You are an autonomous agent that converts an online article into an engaging multi-speaker podcast.
Work through the following steps. ALWAYS execute a step only after the previous one is fully complete.
Return your final answer strictly via the structured output model.

Step-by-step workflow:
1. Identify: Extract the variables `target_url` and `num_hosts` from the user prompt.
2. Extraction: Call `extract_text_from_url` on `target_url` to obtain the main human-readable text.
   • If extraction fails or returns <500 characters, stop and report an error.
   • Limit the stored text to the first 8 000 characters to keep context size reasonable.
3. Script Writing: Invoke `generate_podcast_script_with_llm`, passing the extracted text and `num_hosts`.
   • Ensure the script clearly labels each host (e.g., Host 1:, Host 2: …).
   • The script should include an intro, main discussion, and outro.
4. Audio Generation: Use `generate_audio_script` from the ElevenLabs MCP server to turn the script into narrated audio.
   • Pass the full script string; let the server select default voices if none specified.
   • Capture the returned file path (or URL) of the generated MP3.
5. Produce the final structured JSON object with keys: url, extracted_text, podcast_script, audio_file_path.
   • Truncate `extracted_text` to 1 500 characters if it exceeds that length.
   • Do NOT include any supplementary commentary outside the JSON model.
"""

# ========== Tools definition ==========
TOOLS = [
    extract_text_from_url,
    generate_podcast_script_with_llm,
    # ElevenLabs MCP server for text-to-speech
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
            "generate_audio_script",  # minimal tool needed for this task
        ],
    ),
]

# ========== Agent creation ==========
agent = AnyAgent.create(
    "openai",
    AgentConfig(
        model_id="o3",
        instructions=INSTRUCTIONS,
        tools=TOOLS,
        output_type=PodcastOutput,
        model_args={"tool_choice": "required"},
    ),
)

# ========== CLI Runner ==========
PROMPT_TEMPLATE = (
    """Create a {num_hosts}-host podcast from this article URL.\n"""
    "URL: {url}"
)

def run_agent(url: str, num_hosts: int = 2):
    """Generate a multi-speaker podcast from a webpage URL."""
    input_prompt = PROMPT_TEMPLATE.format(url=url, num_hosts=num_hosts)

    try:
        agent_trace = agent.run(prompt=input_prompt, max_turns=20)
    except AgentRunError as e:
        # Capture partial trace if the agent fails mid-run
        agent_trace = e.trace
        print(f"Agent execution failed: {e}")
        print("Retrieved partial agent trace…")

    # Save trace for evaluation
    with open("generated_workflows/latest/agent_eval_trace.json", "w", encoding="utf-8") as f:
        f.write(agent_trace.model_dump_json(indent=2))

    # Return structured final output only
    return agent_trace.final_output

if __name__ == "__main__":
    Fire(run_agent)