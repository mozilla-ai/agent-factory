
# agent.py

# good to have
import os

# ALWAYS used
import json
from pathlib import Path
from dotenv import load_dotenv
from any_agent import AgentConfig, AnyAgent, AgentRunError
from pydantic import BaseModel, Field
from fire import Fire

# ADD BELOW HERE: tools made available by any-agent or agent-factory
from typing import Literal, List
from any_agent.config import MCPStdio
from tools.extract_text_from_url import extract_text_from_url
from tools.generate_podcast_script_with_llm import generate_podcast_script_with_llm
from tools.combine_mp3_files_for_podcast import combine_mp3_files_for_podcast

load_dotenv()

# ========== Structured output definition ==========
class DialogSegment(BaseModel):
    speaker: Literal["Host", "Guest"] = Field(..., description="Speaker label (Host or Guest).")
    text: str = Field(..., description="Text spoken by the speaker in this segment.")
    audio_file: str = Field(..., description="Path to the generated mp3 file for this segment.")

class StructuredOutput(BaseModel):
    final_podcast_mp3: str = Field(..., description="Path to the final combined podcast mp3 file.")
    segments: List[DialogSegment] = Field(..., description="Ordered list of dialogue segments with corresponding audio files.")

# ========== System (Multi-step) Instructions ===========
INSTRUCTIONS='''
You are a podcast-production assistant that follows this precise multi-step workflow to create a 1-minute podcast from a webpage URL:
STEP 1 – Extract Source Text
•   Receive the webpage URL from the user.
•   Call `extract_text_from_url(url=<user URL>)` to fetch and return the main textual content (ignore navigation, ads, etc.).

STEP 2 – Draft Podcast Script
•   Call `generate_podcast_script_with_llm` with arguments:
    – `text`  = extracted content from STEP 1
    – `num_speakers` = 2
    – `style` = "friendly interview"
    – `max_words` ≈ 160 (≈1-minute spoken audio)
•   The tool returns a JSON list of dialogue turns in order, each turn containing:
        {"speaker": "Host"|"Guest", "text": "…"}
•   Ensure the list alternates speakers starting with Host and ending with Host or Guest such that total script length ≈ 1 minute.

STEP 3 – Text-to-Speech for Each Turn
•   For each dialogue turn i (preserve order):
     – If speaker == "Host", call `text_to_speech` with `text=<turn text>`, `voice_name`="Adam" (or user-provided host voice), `output_filename` = f"host_{i}.mp3".
     – If speaker == "Guest", call `text_to_speech` with `text=<turn text>`, `voice_name`="Rachel" (or user-provided guest voice), `output_filename` = f"guest_{i}.mp3".
•   Collect generated mp3 file paths in the same order as the dialogue list.

STEP 4 – Combine Audio Files
•   Call `combine_mp3_files_for_podcast(mp3_file_paths=<ordered list>, output_filename="podcast_final.mp3")` to merge individual segments into one seamless podcast file.

STEP 5 – Return Structured Output
Return a JSON object following the `StructuredOutput` schema:
{
  "final_podcast_mp3": "podcast_final.mp3",
  "segments": [
        {"speaker": "Host",  "text": "…", "audio_file": "host_1.mp3"},
        {"speaker": "Guest", "text": "…", "audio_file": "guest_2.mp3"},
        …
  ]
}
General Rules:
•   Always respect the step order; do not skip or reorder steps.
•   Only call the specified tools with the minimal required arguments.
•   Keep total dialogue length to ~160 words for ~60 seconds of speech.
•   Never fabricate content; base the script on the extracted webpage text.
•   If any step fails, return a clear error message in the corresponding field.
'''

# ========== Tools definition ===========
from any_agent.config import MCPStdio
import os
from tools.extract_text_from_url import extract_text_from_url
from tools.generate_podcast_script_with_llm import generate_podcast_script_with_llm
from tools.combine_mp3_files_for_podcast import combine_mp3_files_for_podcast

TOOLS = [
    extract_text_from_url,
    generate_podcast_script_with_llm,
    combine_mp3_files_for_podcast,
    # ElevenLabs text-to-speech via MCP
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
            "text_to_speech",
        ],
    ),
]

 

# ========== Running the agent via CLI ===========
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

def main(url: str):
    """Generate a 1-minute podcast mp3 from the textual content of the provided webpage URL, using interleaved dialogue between a Host and a Guest, and return paths of generated audio files in structured form."""
    input_prompt = f"Create a 1-minute podcast based on the content at this URL: {url}"
    try:
        agent_trace = agent.run(prompt=input_prompt, max_turns=20)
    except AgentRunError as e:
        agent_trace = e.trace
        print(f"Agent execution failed: {str(e)}")
        print("Retrieved partial agent trace...")

    # Extract cost information (with error handling)
    try:
        cost_info = agent_trace.cost
        if cost_info.total_cost > 0:
            cost_msg = (
                f"input_cost=${cost_info.input_cost:.6f} + "
                f"output_cost=${cost_info.output_cost:.6f} = "
                f"${cost_info.total_cost:.6f}"
            )
    except Exception:
        class DefaultCost:
            input_cost = 0.0
            output_cost = 0.0
            total_cost = 0.0
        cost_info = DefaultCost()

    # Create enriched trace data with costs as separate metadata
    script_dir = Path(__file__).resolve().parent
    output_path = script_dir / "agent_eval_trace.json"

    # Prepare the trace data with costs
    trace_data = agent_trace.model_dump()
    trace_data["execution_costs"] = {
        "input_cost": cost_info.input_cost,
        "output_cost": cost_info.output_cost,
        "total_cost": cost_info.total_cost
    }

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(json.dumps(trace_data, indent=2))

    return agent_trace.final_output

if __name__ == "__main__":
    Fire(main)

