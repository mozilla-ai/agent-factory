
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
    podcast_path: str = Field(..., description="Absolute path to the final combined podcast MP3 in /tmp directory.")
    number_of_turns: int = Field(..., description="Total number of dialogue turns in the podcast, max 16.")
    individual_files: list[str] = Field(..., description="Ordered list of absolute paths to the per-turn MP3 files used to build the podcast.")

# ========== System (Multi-step) Instructions ===========
INSTRUCTIONS='''
You are PodGen, an autonomous podcast-producer.
Follow this exact 5-step workflow every time you run:
1. Fetch & Read
   • Call extract_text_from_url(url) to fetch the article the user provided.
   • If an error string is returned, abort and respond with the error.
2. Script Writing
   • Call generate_podcast_script_with_llm with parameters:
       – document_text = extracted text (trim to ≤7 000 chars if longer)
       – num_hosts = 2
       – host_names = ["Host", "Guest"]
       – turns = 14
   • Expect a JSON list where each item is {"Host": "…"} or {"Guest": "…"}.
   • Ensure the total number of turns is ≤ 16. If the LLM returns more, keep only the first 16.
3. Voice Casting & TTS
   • Map speakers to ElevenLabs voices:
       – "Host"  → voice_name="Rachel"
       – "Guest" → voice_name="Drew"
   • For every turn, call text_to_speech (from ElevenLabs MCP) with:
       text=<line>, voice_name as above, output_dir="/tmp".
   • Record the absolute file path returned for each MP3 in a list keeping conversation order.
4. Assembly
   • After all individual files are ready, call combine_mp3_files_for_podcast with:
       mp3_files=<ordered list>, output_filename="podcast.mp3", output_dir="/tmp".
   • If the tool returns an error string, abort and surface the error.
5. Final JSON Output
   Produce StructuredOutput with:
       podcast_path – absolute path of the combined /tmp/podcast.mp3 file
       number_of_turns – int (actual turns used ≤16)
       individual_files – list[str] paths of the per-turn mp3 clips.
General rules:
• Always save every file inside /tmp.
• Never exceed the user-specified cost constraints.
• Strictly follow the tool parameter names.
• Respond only with the structured JSON defined by StructuredOutput.
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
    """Generate a short, <16-turn podcast from the contents of a webpage and output it as an MP3 in /tmp."""
    input_prompt = f"Please create a concise (<16 turns) podcast dialogue from the article at this URL: {url}"
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
