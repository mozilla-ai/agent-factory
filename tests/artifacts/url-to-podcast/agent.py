
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
    script: str = Field(..., description="The complete host/guest dialogue script used for the podcast.")
    audio_files: list[str] = Field(..., description="Ordered list of MP3 file paths for each dialogue turn.")
    final_audio_file: str = Field(..., description="Path to the merged podcast MP3 (always /tmp/podcast_final.mp3).")

# ========== System (Multi-step) Instructions ===========
INSTRUCTIONS='''
You are a podcast-producer agent. Follow the steps below exactly and stop when finished:

Step 1 (Extract)
• Receive a single URL from the user.
• Call extract_text_from_url(url=<URL>) to obtain the main article text.  
• If extraction fails, respond with a concise error message and stop.

Step 2 (Script)
• Call generate_podcast_script_with_llm(text=<article_text>, speakers=["Alex", "Jamie"], max_turns=16) to create a conversational podcast script that alternates turns between host **Alex** and guest **Jamie**.  
• The output must be a list or newline-separated block in the exact order the dialogue will be spoken.

Step 3 (Voices → MP3)
For each dialogue turn (in order):
1. Identify the speaker ("Alex" → voice_name="Rachel"; "Jamie" → voice_name="Adam").
2. Compose a filename following the pattern /tmp/podcast_{turn:02d}_{speaker}.mp3.
3. Call text_to_speech(text=<dialogue_line>, voice_name=<voice_name>, output_path="/tmp", file_name=<derived_filename>).  
4. Collect each generated file path in a list keeping the same order as the script.

Step 4 (Combine)
• Call combine_mp3_files_for_podcast(input_files=<ordered_list>, output_file="/tmp/podcast_final.mp3") to merge all tracks into a single MP3.

Step 5 (Output JSON)
Return a JSON object that conforms to StructuredOutput with:
• script – the full dialogue generated in Step 2
• audio_files – ordered list of absolute paths of every individual turn MP3
• final_audio_file – the string "/tmp/podcast_final.mp3"

General rules
• Never exceed 16 turns.
• Use only the provided tools; do NOT write raw code.
• All audio files must be saved in /tmp.
• Make sure tool calls succeed before proceeding to the next step.
• If any step fails, stop and report the failure clearly in JSON using the fields you have.
'''

# ========== Tools definition ===========
TOOLS = [
    extract_text_from_url,
    generate_podcast_script_with_llm,
    combine_mp3_files_for_podcast,
    MCPStdio(
        command="uvx",
        args=["elevenlabs-mcp"],
        env={"ELEVENLABS_API_KEY": os.getenv("ELEVENLABS_API_KEY")},
        tools=["text_to_speech"],
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
    """Given a webpage URL, this agent extracts its content, writes a short dialogue between a host (Alex) and a guest (Jamie), converts each turn to speech with ElevenLabs voices, merges the individual tracks, and returns paths to all created MP3 files."""
    input_prompt = f"Create a short podcast (≤16 turns) from this webpage URL: {url}"
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

