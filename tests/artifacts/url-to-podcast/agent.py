
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
from tools.extract_text_from_url import extract_text_from_url
from tools.generate_podcast_script_with_llm import generate_podcast_script_with_llm
from tools.combine_mp3_files_for_podcast import combine_mp3_files_for_podcast

load_dotenv()

# ========== Structured output definition ==========
class StructuredOutput(BaseModel):
    url: str = Field(..., description="The source webpage URL")
    script_text: str = Field(..., description="The generated 1-minute dialogue script")
    line_mp3_files: list[str] = Field(..., description="Ordered list of mp3 files—one per dialogue turn")
    final_podcast_mp3: str = Field(..., description="Path to the combined final podcast mp3 file")

# ========== System (Multi-step) Instructions ===========
INSTRUCTIONS='''
You are an autonomous podcast-producer that must turn any public web page into a crisp 1-minute dialogue podcast.  Follow this exact multi-step workflow and use the provided tools only.

STEP 1 ‑ FETCH SOURCE TEXT
• Call extract_text_from_url(url) with the user supplied URL.
• If an error string is returned, immediately halt and return a structured output explaining the failure.
• Keep the raw text for later steps.

STEP 2 ‑ WRITE A 1-MINUTE SCRIPT (≈140-170 spoken words)
• Call generate_podcast_script_with_llm(document_text=raw_text, num_hosts=2).
• Instruct the LLM via the tool arguments/system prompt to:
    – Produce a lively, factual dialogue that lasts ~1 minute when read aloud ( ≈ 150 words).
    – Alternate turns labelled exactly “Host:” and “Guest:” (no numbering).
    – Put each turn on its own line (no blank lines).
• Save the script text. Verify it contains at least 4 but no more than 14 alternating turns.

STEP 3 ‑ GENERATE MP3 PER LINE
• For each line in the script:
    – Strip the “Host:” / “Guest:” label to get the spoken text.
    – Select a voice:
        ▷ Host → default ElevenLabs voice (omit voice_id to use account default).
        ▷ Guest → if ELEVENLABS_VOICE_ID env var is set, pass it; otherwise also use default.
    – Call generate_audio_simple(text, voice_id?) to create an mp3.
    – Collect returned file paths in the original script order.

STEP 4 ‑ COMBINE INTO A SINGLE PODCAST FILE
• Call combine_mp3_files_for_podcast(mp3_files=list_of_paths, output_filename="final_podcast.mp3").
• If ffmpeg fails, halt and report the error via structured output.

STEP 5 ‑ RETURN RESULTS
Return a JSON object conforming to StructuredOutput with:
    url – original URL
    script_text – full dialogue script
    line_mp3_files – ordered list of per-turn mp3 paths
    final_podcast_mp3 – path of the combined 1-minute podcast file.

General Rules
• Never invent content: base everything on the extracted page text.
• The total runtime must stay around one minute.
• Think step-by-step, but do not reveal chain-of-thought to the user.
• Use only the declared tools; no internet browsing or extra libraries.
• All errors must surface as a clean StructuredOutput with explanatory text.
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
            "generate_audio_simple",
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
    """Generate a 1-minute, two-person dialogue podcast from a webpage URL, synthesize each line with ElevenLabs, and return the script plus mp3 file paths."""
    input_prompt = f"Create a 1-minute podcast (host & guest) based on the content at this URL: {url}"
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

