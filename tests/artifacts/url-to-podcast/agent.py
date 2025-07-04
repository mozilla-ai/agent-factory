
# agent.py

# good to have
import os

# ALWAYS used
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
    podcast_path: str = Field(..., description="Absolute path to the final 1-minute podcast MP3 file.")
    segment_paths: list[str] = Field(..., description="Ordered list of individual MP3 segment paths (Host/Guest turns).")
    script: str = Field(..., description="The complete dialogue script that was voiced.")

# ========== System (Multi-step) Instructions ===========
INSTRUCTIONS='''
You are a podcast-production assistant that creates a 1-minute dialogue podcast from a user-supplied webpage URL.  Follow this exact 5-step workflow and do not skip or reorder steps.

Step 1 – Extract source text
• Use extract_text_from_url(url) to fetch and extract all visible text.
• If an error string is returned, stop and reply with the error in `podcast_path`.

Step 2 – Draft the podcast script
• Call generate_podcast_script_with_llm(document_text=extracted_text, num_hosts=2) and ask the model to limit the whole dialogue to ≈150–170 words (≈1 minute spoken).  Make sure the script alternates turns labelled exactly as “Host:” and “Guest:”.
• Verify both speakers have at least two turns.  If not, add brief lines to balance.

Step 3 – Create individual MP3 segments
• Split the script into separate utterances by speaker turn, preserving order.
• For every line, invoke generate_audio_simple(text) from the ElevenLabs MCP server:
  – If the speaker label is “Host:” use the default voice.
  – If the speaker label is “Guest:” override with ELEVENLABS_GUEST_VOICE_ID (if provided in the environment) by passing the voice_id field; otherwise use the server default voice.
• Save the returned MP3 file path into a list maintaining dialogue order.

Step 4 – Merge the dialogue
• Pass the ordered list of MP3 paths to combine_mp3_files_for_podcast(mp3_files).  Name the final file “one_minute_podcast.mp3”.
• If the function returns an error string, stop and place the error in `podcast_path`.

Step 5 – Final structured reply
Return a JSON object that matches the StructuredOutput schema:
• podcast_path – absolute path to the merged MP3
• segment_paths – the ordered list of intermediate MP3 file paths
• script – the full text of the podcast script that was voiced.

General rules
• Only call tools that are listed in TOOLS.
• Keep internal reasoning out of the final answer; output must be valid JSON only.
• Limit total runtime to 20 turns.
'''

# ========== Tools definition ===========
from any_agent.config import MCPStdio

TOOLS = [
    extract_text_from_url,                 # Step 1 – pull webpage text
    generate_podcast_script_with_llm,      # Step 2 – craft dialogue script
    combine_mp3_files_for_podcast,         # Step 4 – merge audio
    MCPStdio(                              # ElevenLabs text-to-speech services (Step 3)
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
            "generate_audio_simple",      # minimal tool needed
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
    """Generate a 1-minute, two-speaker podcast from a webpage and produce an MP3 file."""
    input_prompt = f"Create a 1-minute podcast with alternating Host and Guest dialogue from the contents of this URL: {url}"
    try:
        agent_trace = agent.run(prompt=input_prompt, max_turns=20)
    except AgentRunError as e:
        agent_trace = e.trace
        print(f"Agent execution failed: {str(e)}")
        print("Retrieved partial agent trace...")

    script_dir = Path(__file__).resolve().parent
    output_path = script_dir / "agent_eval_trace.json"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(agent_trace.model_dump_json(indent=2))

    return agent_trace.final_output

if __name__ == "__main__":
    Fire(main)

