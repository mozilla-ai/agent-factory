# agent.py

import os
import json
from pathlib import Path

from dotenv import load_dotenv
from any_agent import AgentConfig, AnyAgent, AgentRunError
from any_agent.config import MCPStdio
from pydantic import BaseModel, Field
from fire import Fire

# ==== Local (python) tools ====
from tools.extract_text_from_url import extract_text_from_url
from tools.generate_podcast_script_with_llm import generate_podcast_script_with_llm
from tools.combine_mp3_files_for_podcast import combine_mp3_files_for_podcast

# NOTE: the ElevenLabs MCP server supplies the text-to-speech tool we need

load_dotenv()

# =============================================================
#                 Structured output definition
# =============================================================
class StructuredOutput(BaseModel):
    url: str = Field(..., description="The original webpage URL that was converted into a podcast.")
    podcast_path: str = Field(..., description="Absolute path of the generated podcast MP3 file.")
    num_hosts: int = Field(..., description="Number of distinct hosts / speakers used in the podcast audio.")
    script_excerpt: str = Field(..., description="First 500 characters of the generated podcast script – useful for quick review.")

# =============================================================
#                 Multi-step system instructions
# =============================================================
INSTRUCTIONS = """
You are an autonomous agent that transforms the content of a web page into an engaging multi-speaker audio podcast.
Follow these steps precisely and ONLY use the provided callable tools to accomplish each step:

1. Receive the user-supplied webpage URL (variable {url}) and the desired number of podcast hosts (variable {num_hosts}).
2. Call `extract_text_from_url` to pull the main readable text from the page.  If an error string is returned, stop and report failure.
3. Condense / adapt that text into an interesting podcast script by calling `generate_podcast_script_with_llm`.  Ensure the script clearly labels each host line as “Host 1: …”, “Host 2: …”, etc.  Keep the dialogue natural and informative.
4. For EACH line in the script:
   a. Pass the plain text line to the ElevenLabs MCP tool `generate_audio_simple` to create an MP3 segment.
   b. Capture the returned file path (or job identifier that resolves to a file path) and maintain the original script order when storing these paths.
5. After all lines have been voiced, call `combine_mp3_files_for_podcast` with the ordered list of MP3 segment paths to merge them into a single podcast MP3.
6. Return a StructuredOutput JSON object containing:
   • url – the original page URL
   • podcast_path – absolute path to the combined podcast file
   • num_hosts – how many distinct host voices were used
   • script_excerpt – the first 500 characters of the generated script (for quick review)

DO NOT include any other keys or free-text outside the structured JSON response.
"""

# =============================================================
#                        Tools list
# =============================================================
TOOLS = [
    # Local python tools
    extract_text_from_url,
    generate_podcast_script_with_llm,
    combine_mp3_files_for_podcast,
    # MCP server providing ElevenLabs TTS capability
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
            "generate_audio_simple",  # simplest text-to-speech endpoint
        ],
    ),
]

# =============================================================
#                       Agent creation
# =============================================================
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

# =============================================================
#                 CLI wrapper around the agent
# =============================================================
PROMPT_TEMPLATE = (
    "Create a multi-speaker podcast with {num_hosts} hosts from the contents of this webpage: {url}. "
    "Follow the step-by-step workflow you have been given."
)


def run_agent(url: str, num_hosts: int = 2):
    """Generate an audio podcast (MP3) from a webpage URL."""

    # Ensure the output directory for traces exists
    Path("generated_workflows/latest").mkdir(parents=True, exist_ok=True)

    input_prompt = PROMPT_TEMPLATE.format(url=url, num_hosts=num_hosts)

    try:
        agent_trace = agent.run(prompt=input_prompt, max_turns=30)
    except AgentRunError as e:
        agent_trace = e.trace  # capture partial trace for debugging
        print(f"Agent execution failed: {str(e)}")
        print("Retrieved partial agent trace…")

    # Save the trace for inspection / evaluation
    with open("generated_workflows/latest/agent_eval_trace.json", "w", encoding="utf-8") as f:
        f.write(agent_trace.model_dump_json(indent=2))

    # Return the final structured result
    return agent_trace.final_output


if __name__ == "__main__":
    Fire(run_agent)