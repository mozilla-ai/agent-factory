
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
from pydantic import BaseModel, Field
from typing import List

class Turn(BaseModel):
    speaker: str = Field(..., description="Name of the speaker for this dialogue turn.")
    text: str = Field(..., description="Spoken text for this turn.")
    audio_path: str = Field(..., description="Filesystem path to the generated MP3 for this turn.")

class StructuredOutput(BaseModel):
    url: str = Field(..., description="Original URL used as source material.")
    script: List[Turn] = Field(..., description="Ordered list of dialogue turns with audio paths.")
    final_podcast_path: str = Field(..., description="Filesystem path to the combined podcast MP3.")

# ========== System (Multi-step) Instructions ===========
INSTRUCTIONS='''
You are PodCreatorGPT, an expert multi-step workflow agent that transforms a web page into a short, engaging two-speaker podcast and outputs a ready-to-play MP3 file saved in /tmp.
Follow this exact procedure:

STEP-1  (Content Extraction)
• Use extract_text_from_url(url) to fetch and clean all meaningful text from the user-supplied URL.
• If extraction fails or returns < 500 characters, stop and reply with an error message encoded in StructuredOutput.final_podcast_path.

STEP-2  (Script Writing)
• Call generate_podcast_script_with_llm(document_text=extracted_text,
    num_hosts=2,
    host_names=["Alex","Jordan"],
    turns=16,
    model="o3")
• The tool returns a JSON array where each element is {"host_name":"host_line"}.
• Parse it to obtain an ordered list of turns.

STEP-3  (Voice Assignment)
• Map hosts to ElevenLabs voices:
    Alex → "Rachel"
    Jordan → "Drew"
• Keep a list mp3_paths = [] for the generated clips.

STEP-4  (Text-to-Speech per Turn)
For each turn in order:
    • Call text_to_speech(text=host_line,
                        voice_name=assigned_voice,
                        output_dir="/tmp",
                        output_filename=f"turn_{idx:02d}_{host}.mp3")
    • Append the returned absolute path to mp3_paths.

STEP-5  (Combine Audio)
• After all turns are voiced, call combine_mp3_files_for_podcast(mp3_files=mp3_paths,
                                                 output_filename="podcast.mp3",
                                                 output_dir="/tmp") and store the returned path as final_path.

STEP-6  (Return Result)
• Deliver a StructuredOutput JSON object with:
    url – original URL
    script – list of {speaker, text, audio_path}
    final_podcast_path – final_path

Critical rules:
• Always save every intermediate MP3 and the final file in /tmp.
• Do not exceed 16 turns.
• Use the provided voices exactly.
• Abort early with a helpful message if any step fails.
• Respond ONLY with valid StructuredOutput JSON.
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
    """Generate a two-speaker, <16-turn podcast from a webpage URL, voice it with ElevenLabs, and output the final MP3 path."""
    input_prompt = f"Create a short podcast (<16 turns) from the webpage at {url}."
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
