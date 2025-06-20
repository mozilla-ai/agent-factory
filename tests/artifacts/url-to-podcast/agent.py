# agent.py

import os
from typing import List

from dotenv import load_dotenv
from any_agent import AnyAgent, AgentConfig
from any_agent.config import MCPStdio
from pydantic import BaseModel, Field
from fire import Fire

# ====== Import tool functions ======
from tools.extract_text_from_url import extract_text_from_url
from tools.generate_podcast_script_with_llm import generate_podcast_script_with_llm
from tools.combine_mp3_files_for_podcast import combine_mp3_files_for_podcast

load_dotenv()

# ========= Structured output definition =========
class PodcastGenerationOutput(BaseModel):
    """Structured response returned by the agent once the podcast is generated."""

    podcast_path: str = Field(..., description="Relative path to the final combined podcast MP3 file.")
    script_text: str = Field(..., description="The full podcast script that was used for voice generation.")
    voices_used: List[str] = Field(..., description="List of voice IDs that were used, in the order they appeared in the script.")


# ========= System (Multi-step) Instructions =========
INSTRUCTIONS = """
You are an AI assistant that turns any webpage into a multi-speaker audio podcast.  
Follow this four-step workflow strictly:

1. Extract   
   • Use the `extract_text_from_url` tool to fetch the main readable text from the provided URL.  
   • Remove boilerplate (navigation, ads, footer) and keep the core article.

2. Script   
   • Write a lively podcast script with the `generate_podcast_script_with_llm` tool.  
   • Number of hosts = number of voice IDs provided by the user (minimum 2; default 2 if none supplied).  
   • The script must alternate between hosts, be engaging, and cover the entire article content concisely.

3. Voice   
   • Convert the script into audio with the `generate_audio_script` tool from the ElevenLabs MCP server.  
   • Provide a JSON payload of the form:  
     `{ "script": [ {"text": "...", "voice_id": "<voice_id_1>", "actor": "Host-1"}, ... ] }`  
   • Map each host to the corresponding `voice_id` in round-robin order if hosts > voices supplied.

4. Combine   
   • Merge all returned MP3 segments into a single podcast episode using `combine_mp3_files_for_podcast`.  
   • Name the output file `podcast_episode.mp3` and save it in the current working directory.

Return ONLY a JSON object that conforms to PodcastGenerationOutput.  
Do NOT include any additional keys or text outside the JSON.
"""

# ========= Tools definition =========
TOOLS = [
    extract_text_from_url,
    generate_podcast_script_with_llm,
    # ElevenLabs MCP server – only the tool we need (generate_audio_script)
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
        tools=["generate_audio_script"],
    ),
    combine_mp3_files_for_podcast,
]

# ========= Agent definition =========
agent = AnyAgent.create(
    "openai",
    AgentConfig(
        model_id="o3",
        instructions=INSTRUCTIONS,
        tools=TOOLS,
        output_type=PodcastGenerationOutput,
        # Require the model to invoke tools when needed
        model_args={"tool_choice": "required"},
    ),
)

# ========= Runner =========
PROMPT_TEMPLATE = (
    "Create a multi-speaker podcast from this URL: {url}. "
    "Use these voice IDs (comma-separated, leave blank for defaults): {voice_ids}."
)

def run_agent(url: str, voice_ids: str = "") -> PodcastGenerationOutput:  # noqa: D401
    """Generate an audio podcast from the given URL.

    Args:
        url: Webpage URL to turn into a podcast.
        voice_ids: Comma-separated ElevenLabs voice IDs (optional).
    Returns:
        PodcastGenerationOutput structured object.
    """
    # Build prompt for the agent
    input_prompt = PROMPT_TEMPLATE.format(url=url, voice_ids=voice_ids.strip())

    agent_trace = agent.run(prompt=input_prompt, max_turns=20)

    # Persist trace for evaluation
    os.makedirs("generated_workflows/latest", exist_ok=True)
    with open("generated_workflows/latest/agent_eval_trace.json", "w", encoding="utf-8") as f:
        f.write(agent_trace.model_dump_json(indent=2))

    # Return the structured final output
    return agent_trace.final_output


if __name__ == "__main__":
    Fire(run_agent)