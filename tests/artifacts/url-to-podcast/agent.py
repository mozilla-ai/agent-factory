
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
from typing import List

class StructuredOutput(BaseModel):
    url: str = Field(..., description="Original webpage URL provided by the user.")
    script_json: str = Field(..., description="JSON list representing the host/guest dialogue.")
    audio_files: List[str] = Field(..., description="Ordered list of individual MP3 files for each dialogue turn.")
    final_podcast: str = Field(..., description="Absolute path to the combined podcast MP3 file saved in /tmp.")

# ========== System (Multi-step) Instructions ===========
INSTRUCTIONS='''
You are a podcast-producer agent. Follow this concise multi-step workflow whenever the user provides a webpage URL.

STEP 1 – Retrieve source text
• Invoke extract_text_from_url(url=<USER_URL>) to fetch the full plaintext of the page.
• If the fetch fails, stop and respond with an error.

STEP 2 – Draft podcast script (≤ 16 turns)
• Call generate_podcast_script_with_llm(document_text=<STEP1_TEXT>,
                                         num_hosts=2,
                                         host_names=["Alex","Jordan"],
                                         turns=16,
                                         model="o3")
  This returns a JSON list where each element is {"<speaker>": "<line>"}.
• Save this raw JSON string so it can be echoed in the final output.

STEP 3 – Convert lines to speech
For every item in the returned JSON list (maintaining order):
  • Determine the speaker name (key) and line (value).
  • Choose a voice_name for ElevenLabs text_to_speech:
        – "Alex" → voice_name="Adam"
        – "Jordan" → voice_name="Bella"
  • Call text_to_speech(text=<line>, voice_name=<chosen>, directory="/tmp").
  • Collect the absolute path of the resulting MP3 file in order.

STEP 4 – Merge audio clips
• After all clips are generated, call combine_mp3_files_for_podcast(
        mp3_files=<ORDERED_LIST>,
        output_filename="podcast.mp3",
        output_dir="/tmp"
  ) to create /tmp/podcast.mp3.

STEP 5 – Return structured JSON
Provide output using StructuredOutput with:
  url – original URL
  script_json – the JSON script from STEP 2
  audio_files – ordered list of individual MP3 files
  final_podcast – absolute path of /tmp/podcast.mp3

GENERAL RULES
• Never hallucinate file paths—use those returned by tools.
• Keep conversation to ≤ 16 turns.
• If any step fails, report the failure clearly in structured output.
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
    print(f"Error connecting to mcpd: {e}", file=sys.stderr)

# ========== Running the agent via CLI ===========
agent = AnyAgent.create(
    "openai",
    AgentConfig(
        model_id="o3",
        instructions=INSTRUCTIONS,
        tools=TOOLS,
        output_type=StructuredOutput,  # name of the Pydantic v2 model defined above
        model_args={"tool_choice": "auto"},
    ),
)


def main(url: str):
    """Generate an engaging <16-turn podcast from a webpage, synthesize each line via ElevenLabs TTS, and output the merged MP3."""
    input_prompt = f"Create a short podcast (max 16 turns) from this URL: {url}"
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
