# agent.py

import os
from dotenv import load_dotenv
from any_agent import AgentConfig, AnyAgent
from any_agent.config import MCPStdio
from pydantic import BaseModel, Field
from fire import Fire

# === Local / built-in tools ===
from tools.extract_text_from_url import extract_text_from_url
from tools.generate_podcast_script_with_llm import generate_podcast_script_with_llm
# (We will rely on the ElevenLabs MCP server for text-to-speech)

load_dotenv()

# ========== Structured output definition ==========
class PodcastOutput(BaseModel):
    url: str = Field(..., description="The original webpage URL.")
    num_speakers: int = Field(..., description="Number of speakers in the generated podcast.")
    podcast_script: str = Field(..., description="The full podcast script with speaker labels.")
    audio_file_path: str = Field(..., description="Filesystem path (or URL) to the generated podcast MP3 audio file.")


# ========== System (Multi-step) Instructions ==========
INSTRUCTIONS = """
You are an expert media production assistant.  Follow this exact multi-step workflow to turn an input webpage
into a multi-speaker podcast:

Step 1 ‑ Extract text.
    • Use the tool `extract_text_from_url` on the provided URL.
    • Return ONLY the primary readable content (ignore menus, ads, navigation, etc.).

Step 2 ‑ Write a podcast script.
    • Use `generate_podcast_script_with_llm`.
    • The number of hosts MUST equal the `num_speakers` value supplied by the user (default 2).
    • Clearly label each host line (e.g. Host 1:, Host 2: …).
    • The script should be lively, conversational and cover all key points from the article.

Step 3 ‑ Generate audio with multiple voices.
    • Call the ElevenLabs MCP tool `generate_audio_script`.
    • Pass the full script in plain text. The tool will automatically allocate different voices for each labelled host.
    • Wait until the audio job finishes and obtain the final MP3 file path returned by the tool.

Step 4 ‑ Produce final structured result.
    • Return a JSON object conforming to the PodcastOutput schema containing:
         – url (original URL)
         – num_speakers (integer)
         – podcast_script (full script)
         – audio_file_path (path/URL from Step 3)
    • Do NOT output anything that does not belong in the JSON schema.
"""

# ========== Tools definition ==========
TOOLS = [
    # Local python-function tools
    extract_text_from_url,
    generate_podcast_script_with_llm,
    # MCP server for ElevenLabs TTS
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
            "generate_audio_script",  # only tool we need from this MCP server
        ],
    ),
]

# ========== Agent instance ==========
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

# ========== CLI entry-point ==========

def run_agent(url: str, num_speakers: int = 2):
    """Generate a multi-speaker podcast from a webpage URL."""
    # Compose the user prompt that kicks off the workflow
    input_prompt = (
        "Create a podcast with {n} speakers from this webpage URL: {u}. "
        "Return the final result using the required JSON schema.".format(n=num_speakers, u=url)
    )

    agent_trace = agent.run(prompt=input_prompt, max_turns=20)

    # Persist the full trace for evaluation
    with open("generated_workflows/latest/agent_eval_trace.json", "w", encoding="utf-8") as f:
        f.write(agent_trace.model_dump_json(indent=2))

    return agent_trace.final_output


if __name__ == "__main__":
    Fire(run_agent)