# agent.py

import os

from any_agent import AgentConfig, AnyAgent
from any_agent.config import MCPStdio
from dotenv import load_dotenv
from fire import Fire
from pydantic import BaseModel, Field

# ===== Import callable tools =====
from tools.extract_text_from_url import extract_text_from_url
from tools.generate_podcast_script_with_llm import generate_podcast_script_with_llm

load_dotenv()


# ========= Structured output definition =========
class StructuredOutput(BaseModel):
    url: str = Field(..., description="The original webpage URL that was processed.")
    num_hosts: int = Field(..., description="Number of podcast hosts/speakers requested.")
    script: str = Field(..., description="The generated multi-speaker podcast script.")
    audio_file_path: str = Field(..., description="Local path (or URL) to the final narrated podcast audio file.")


# ========= System (Multi-step) Instructions =========
INSTRUCTIONS = """
You are an autonomous assistant that converts a webpage into a narrated, multi-speaker podcast.
Follow these steps strictly:
1. INPUT: You receive a webpage URL and an integer `num_hosts` specifying the number of podcast speakers.
2. EXTRACTION: Call `extract_text_from_url` to fetch and clean the full textual content of the page.
   • If the function returns an error (string beginning with "Error"), stop and return that error in `script`, leave `audio_file_path` blank.
3. SCRIPT WRITING: Use `generate_podcast_script_with_llm` with `document_text=<extracted_text>` and `num_hosts=<num_hosts>` to craft an engaging dialogue.
   • Ensure host lines are clearly labelled (e.g., "Host 1:", "Host 2:").
4. TTS GENERATION: Invoke the ElevenLabs MCP tool `generate_audio_script`.
   • Pass the entire script as a JSON string in the format: {"script": <SCRIPT_TEXT>}.
   • Let ElevenLabs assign suitable default voices if `voice_id` is omitted.
   • Capture the returned `job_id`.
5. RETRIEVE AUDIO: Use `get_audio_file` with the `job_id` to download or locate the final MP3 file path.
6. OUTPUT: Return a JSON object with these fields strictly matching the `StructuredOutput` model:
   • url – the original URL
   • num_hosts – the integer supplied by the user
   • script – the complete podcast script text
   • audio_file_path – path or URL of the generated MP3
Always follow the steps in order, call only the listed tools, and do not hallucinate tool outputs.
"""

# ========= Tools definition =========
TOOLS = [
    extract_text_from_url,
    generate_podcast_script_with_llm,
    # ElevenLabs MCP – only the two tools we need
    MCPStdio(
        command="docker",
        args=[
            "run",
            "-i",
            "--rm",
            "-e",
            "ELEVENLABS_API_KEY",  # pass through the API key
            "mcp/elevenlabs",
        ],
        env={
            "ELEVENLABS_API_KEY": os.getenv("ELEVENLABS_API_KEY"),
        },
        tools=[
            "generate_audio_script",
            "get_audio_file",
        ],
    ),
]

# ========= Agent creation =========
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

# ========= CLI runner =========


def run_agent(url: str, num_hosts: int = 2):
    """Generate a narrated multi-speaker podcast from a webpage URL."""
    prompt_template = (
        "Create a {num_hosts}-speaker podcast from the content of this webpage: {url}. "
        "Return the structured JSON as specified."
    )
    input_prompt = prompt_template.format(url=url, num_hosts=num_hosts)
    agent_trace = agent.run(prompt=input_prompt)

    # Save trace for evaluation
    os.makedirs("generated_workflows/latest", exist_ok=True)
    with open("generated_workflows/latest/agent_eval_trace.json", "w", encoding="utf-8") as f:
        f.write(agent_trace.model_dump_json(indent=2))

    return agent_trace.final_output


if __name__ == "__main__":
    Fire(run_agent)
