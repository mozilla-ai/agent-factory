
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
import os
from any_agent.config import MCPStdio
from tools.extract_text_from_url import extract_text_from_url
from tools.generate_podcast_script_with_llm import generate_podcast_script_with_llm
from tools.combine_mp3_files_for_podcast import combine_mp3_files_for_podcast

load_dotenv()

# ========== Structured output definition ==========
class StructuredOutput(BaseModel):
    final_mp3_path: str = Field(..., description="Absolute path to the final combined podcast mp3 file.")
    segment_paths: list[str] = Field(..., description="Ordered list of mp3 segment file paths for each dialogue turn.")
    podcast_script: str = Field(..., description="The full Host/Guest script that was converted to audio.")

# ========== System (Multi-step) Instructions ===========
INSTRUCTIONS='''
You are an autonomous production assistant that turns the contents of a webpage into a concise 1-minute podcast (≈150–170 spoken words).  The end product must be a single mp3 that alternates dialogue between a Host and a Guest speaker.

Follow these steps exactly and sequentially:

1. (extract_text_from_url) Receive the URL from the user and extract its readable text.  If extraction fails, stop and respond with an error.

2. (generate_podcast_script_with_llm) Produce a two-speaker podcast script no longer than 170 words (≈1 minute) that captures the key ideas of the extracted text.  Label each turn plainly as “Host:” or “Guest:”.  Keep turns short (1-2 sentences).

3. Parse the script into individual dialogue turns.  Create one mp3 per turn using ElevenLabs text-to-speech:
   • Use generate_audio_simple for each turn.
   • Use the default voice for the Host and the second available voice for the Guest (obtainable via list_voices if needed).  Alternate voices strictly Host/Guest/Host…
   • Save every generated audio file path returned by the tool.

4. (combine_mp3_files_for_podcast) Pass the ordered list of mp3 segment paths to combine_mp3_files_for_podcast to create a final file named "podcast.mp3" under a folder called "podcasts".

5. Return structured JSON with:
   • final_mp3_path – absolute path of the combined mp3
   • segment_paths – ordered list of the individual segment mp3 files
   • podcast_script – the exact text of the script you produced.

Be meticulous: call the appropriate tool for every step, respect the word limit so the audio stays ≈1 minute, and ensure the Host/Guest pattern is preserved.
'''

# ========== Tools definition ===========
from any_agent.config import MCPStdio
from tools.extract_text_from_url import extract_text_from_url
from tools.generate_podcast_script_with_llm import generate_podcast_script_with_llm
from tools.combine_mp3_files_for_podcast import combine_mp3_files_for_podcast

TOOLS = [
    extract_text_from_url,
    generate_podcast_script_with_llm,
    combine_mp3_files_for_podcast,
    # ElevenLabs MCP for text-to-speech
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
            "generate_audio_simple",
            "list_voices",
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
    """Generate a 1-minute two-speaker podcast from a webpage URL, synthesize each line with ElevenLabs voices, combine the audio, and return paths and script."""
    input_prompt = f"Create a 1-minute podcast mp3 based on the following URL: {url}"
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

