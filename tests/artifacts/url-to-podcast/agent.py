
# agent.py

# Always used imports
import json  # noqa: I001
import os
import sys
from pathlib import Path

from any_agent import AgentConfig, AgentRunError, AnyAgent
from dotenv import load_dotenv
from fire import Fire
from mcpd import McpdClient, McpdError
from pydantic import BaseModel, Field

# ADD BELOW HERE: tools made available by any-agent or agent-factory
from tools.extract_text_from_url import extract_text_from_url
from tools.generate_podcast_script_with_llm import generate_podcast_script_with_llm
from tools.combine_mp3_files_for_podcast import combine_mp3_files_for_podcast

load_dotenv()

# Connect to mcpd daemon for accessing available tools
MCPD_ENDPOINT = os.getenv("MCPD_ADDR", "http://localhost:8090")
MCPD_API_KEY = os.getenv("MCPD_API_KEY", None)

# ========== Structured output definition ==========
class StructuredOutput(BaseModel):
    podcast_mp3: str = Field(..., description="Absolute path to the final combined podcast mp3 file saved in /tmp.")
    segment_files: list[str] = Field(..., description="Ordered list of absolute paths of the individual dialogue segment mp3 files.")
    host_voice: str = Field(..., description="Voice name used for the host speaker.")
    guest_voice: str = Field(..., description="Voice name used for the guest speaker.")
    turns: int = Field(..., description="Total number of dialogue turns in the podcast.")

# ========== System (Multi-step) Instructions ===========
INSTRUCTIONS='''
You are a multi-step agent that produces a short podcast MP3 based on the content of a webpage URL supplied by the user. Follow the steps exactly and use the specified tools.

Step 1 – Retrieve article text:
• Use extract_text_from_url to download and extract the readable text from the provided URL.
• If the tool returns an error message, stop and reply with that error.

Step 2 – Generate the podcast dialogue script:
• Speaker names: Host = “Alex”, Guest = “Jordan”.
• Voice mapping: Alex → "Aria", Jordan → "Drew".
• Call generate_podcast_script_with_llm with:
  – document_text = text from Step 1
  – num_hosts = 2
  – host_names = ["Alex", "Jordan"]
  – turns = 16
• The tool returns a JSON list where each item is one turn. Ensure there are ≤ 16 turns.

Step 3 – Create per-turn audio files:
• For each turn in order:
  – Identify the speaker (Alex or Jordan).
  – Call text_to_speech (ElevenLabs MCP) with parameters:
     • text = speaker’s line
     • voice_name = "Aria" if Alex else "Drew"
     • output_dir = "/tmp"
     • output_filename = f"segment_{index:02d}.mp3"
  – Collect the absolute path returned for every segment.

Step 4 – Merge audio segments:
• After all segments are created, call combine_mp3_files_for_podcast with:
  – mp3_files = ordered list of segment paths
  – output_filename = "podcast.mp3"
  – output_dir = "/tmp"
• Verify that a valid path is returned.

Step 5 – Return structured JSON:
Respond ONLY with a StructuredOutput object that contains:
• podcast_mp3 – absolute path to the combined podcast file
• segment_files – ordered list of the segment paths
• host_voice – "Aria"
• guest_voice – "Drew"
• turns – total number of dialogue turns
'''

# ========== Tools definition ===========
TOOLS = [
    extract_text_from_url,
    generate_podcast_script_with_llm,
    combine_mp3_files_for_podcast,
]

try:
    mcpd_client = McpdClient(api_endpoint=MCPD_ENDPOINT, api_key=MCPD_API_KEY)
    mcp_server_tools = mcpd_client.agent_tools()
    if not mcp_server_tools:
        print("No tools found via mcpd.")
    TOOLS.extend(mcp_server_tools)
except McpdError as e:
    print(
        f"Error connecting to mcpd: {e}. If the agent doesn't use any MCP servers you can safely ignore this error",
        file=sys.stderr
    )

# ========== Running the agent via CLI ===========
agent = AnyAgent.create(
    "tinyagent",
    AgentConfig(
        model_id="openai/o3",
        instructions=INSTRUCTIONS,
        tools=TOOLS,
        output_type=StructuredOutput,  # name of the Pydantic v2 model defined above
        model_args={"tool_choice": "auto"},
    ),
)


def main(url: str):
    """Generate a short podcast MP3 (≤16 dialogue turns) from the content of a given webpage URL, using ElevenLabs voices and saving all audio files to /tmp."""
    input_prompt = f"Create a podcast from this URL: {url}"
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
            print(cost_msg)
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

    with output_path.open("w", encoding="utf-8") as f:
        f.write(json.dumps(trace_data, indent=2))

    return agent_trace.final_output


if __name__ == "__main__":
    Fire(main)
