
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
from any_agent.config import MCPStdio
from tools.extract_text_from_url import extract_text_from_url
from tools.generate_podcast_script_with_llm import generate_podcast_script_with_llm
from tools.combine_mp3_files_for_podcast import combine_mp3_files_for_podcast

load_dotenv()

# ========== Structured output definition ==========
class StructuredOutput(BaseModel):
    script: str = Field(..., description="The full podcast script that was voiced.")
    segment_paths: list[str] = Field(..., description="Ordered list of mp3 files generated for each dialogue turn.")
    podcast_path: str = Field(..., description="Absolute path to the final combined podcast mp3 file.")

# ========== System (Multi-step) Instructions ===========
INSTRUCTIONS='''
You are an autonomous agent tasked with creating a one-minute podcast, saved as a single mp3, from the contents of a webpage provided by the user. Follow this fixed 6-step workflow and do not skip any step.

Step 1 – Extract:
  • Use the `extract_text_from_url` tool with the user-supplied URL to fetch and extract clean plain text from the page.  
  • If the tool returns an error, stop immediately and return the error inside the field `podcast_path`.

Step 2 – Script writing:
  • Pass the extracted text to `generate_podcast_script_with_llm` with `num_hosts=2`.  
  • In the prompt ask for a brief, ~1-minute script (≈150-200 spoken words) that alternates lines between a “Host” and a “Guest”.  
  • Ensure every spoken line starts with either “Host:” or “Guest:”.  
  • Save the full script for the final output.

Step 3 – Prepare dialogue turns:
  • Split the script into an ordered list of dialogue lines.  
  • Trim any leading/trailing whitespace.

Step 4 – Voice synthesis:
  • For each dialogue line call `generate_audio_simple` (from the ElevenLabs MCP server).  
  • Provide the line’s text via the `text` argument.  
  • Provide `voice_id` as follows: use the environment variable `ELEVENLABS_HOST_VOICE_ID` for “Host:” lines and `ELEVENLABS_GUEST_VOICE_ID` for “Guest:” lines.  
  • Collect the absolute path of every generated mp3 in the same order as the dialogue.  

Step 5 – Combine:
  • After all lines are voiced, call `combine_mp3_files_for_podcast` with the ordered list of mp3 paths and `output_filename="podcast.mp3"`.  
  • Save the returned path: this is the final podcast file.

Step 6 – Respond:
  • Return a JSON object that matches the StructuredOutput schema:
        script             – the full podcast script
        segment_paths      – list of mp3 paths generated in Step 4 in the exact playback order
        podcast_path       – absolute path of the combined “podcast.mp3”

General rules:
  • Keep the entire podcast around one minute.  
  • Never invent content not present in the source URL.  
  • If any tool returns an error string starting with “Error”, abort remaining steps and include that string in all output fields.  
  • Do not expose internal reasoning; only use the tools and produce the required final JSON.
'''

# ========== Tools definition ===========
# ========= Tools definition =========
from any_agent.config import MCPStdio
from tools.extract_text_from_url import extract_text_from_url
from tools.generate_podcast_script_with_llm import generate_podcast_script_with_llm
from tools.combine_mp3_files_for_podcast import combine_mp3_files_for_podcast
import os

TOOLS = [
    extract_text_from_url,
    generate_podcast_script_with_llm,
    combine_mp3_files_for_podcast,
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
            # Optional voice IDs picked up inside the container
            "ELEVENLABS_VOICE_ID": os.getenv("ELEVENLABS_VOICE_ID"),
            "ELEVENLABS_HOST_VOICE_ID": os.getenv("ELEVENLABS_HOST_VOICE_ID"),
            "ELEVENLABS_GUEST_VOICE_ID": os.getenv("ELEVENLABS_GUEST_VOICE_ID"),
        },
        tools=["generate_audio_simple"],
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
    """Generate a 1-minute two-speaker podcast from a webpage, synthesize each turn with ElevenLabs, and return the paths to all generated audio files."""
    input_prompt = f"Create a 1-minute podcast based on the content of the URL: {url}"
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

