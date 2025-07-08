
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
    final_mp3_path: str = Field(..., description="Absolute path to the combined 1-minute podcast mp3 file.")
    script_text: str = Field(..., description="Full dialogue script used to generate the podcast.")
    segment_files: list[str] = Field(..., description="Ordered list of mp3 file paths created for each dialogue turn.")

# ========== System (Multi-step) Instructions ===========
INSTRUCTIONS='''
You are an assistant that produces a concise (~1-minute) podcast episode in dialogue form (Host ↔ Guest) from the contents of a webpage supplied by the user. Follow this multi-step workflow strictly and only proceed to the next step when the current one succeeds.

1. Content Extraction – TOOL: extract_text_from_url
   • Take the provided URL and extract its main textual content, removing navigation, ads, and footers.
   • If nothing meaningful is found, stop and report an error.

2. Script Writing – TOOL: generate_podcast_script_with_llm
   • Write a podcast script ≈150 spoken words (≈1 minute) featuring exactly two speakers labelled “Host:” and “Guest:”. Speakers should alternate every line (turn-by-turn).
   • Keep language engaging, cover the key ideas of the source page, and ensure a clear intro and outro.

3. Audio Generation – TOOL: generate_audio_script (via ElevenLabs MCP server)
   • Build a JSON payload of the form:
     {
       "script": [
         {"text": "...first line...", "actor": "Host"},
         {"text": "...second line...", "actor": "Guest"},
         ...
       ]
     }
   • DO NOT include voice_id fields unless the user supplied them; the server’s defaults are fine.
   • Call generate_audio_script; it returns a list of mp3 file paths (one per line).

4. Combination – TOOL: combine_mp3_files_for_podcast
   • Confirm the number of returned mp3s equals the number of script lines.
   • Merge them, in order, into a single mp3 named "final_podcast.mp3" inside the "podcasts" folder.

5. Final Output
   • Return a JSON object that conforms to StructuredOutput with:
     – final_mp3_path: absolute path of the combined mp3
     – script_text: full podcast script created in step 2
     – segment_files: ordered list of individual mp3 files
   • If any step fails, populate the relevant field(s) with a clear error message and leave later fields empty.

General Guidelines
• Keep all intermediate files relative to the current working directory.
• Do not hallucinate content not present in the source.
• The entire workflow must stay within 20 turns.
'''

# ========== Tools definition ===========
from any_agent.config import MCPStdio

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
        },
        tools=[
            "generate_audio_script",
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
    """Generate a ~1-minute host-guest podcast mp3 from the textual content of the provided webpage URL."""
    input_prompt = f"Create a 1-minute podcast mp3 from the webpage at: {url}"
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

