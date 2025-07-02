
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
from tools.summarize_text_with_llm import summarize_text_with_llm
from tools.generate_podcast_script_with_llm import generate_podcast_script_with_llm
from tools.combine_mp3_files_for_podcast import combine_mp3_files_for_podcast

load_dotenv()

# ========== Structured output definition ==========
class StructuredOutput(BaseModel):
    url: str = Field(..., description="Original webpage URL provided by the user.")
    summary_text: str = Field(..., description="≈100-word summary used to craft the podcast.")
    script_text: str = Field(..., description="Full podcast dialogue script with speaker labels.")
    individual_audio_files: list[str] = Field(..., description="Ordered list of generated mp3 segment file paths.")
    podcast_file: str = Field(..., description="Absolute path to the final combined 1-minute podcast mp3.")

# ========== System (Multi-step) Instructions ===========
INSTRUCTIONS='''
You are an autonomous podcast-production agent.  Follow this exact step-by-step workflow and use ONLY the provided tools.

1. RECEIVE the target webpage URL from the user.
2. CALL extract_text_from_url(url=<user_url>) to get the raw page text.
   • If an error string is returned, STOP and respond with the error.
3. CALL summarize_text_with_llm(text=<raw_text>, summary_length="a ~100-word paragraph") to condense the content so it comfortably fits ~1 minute of spoken audio.
4. CALL generate_podcast_script_with_llm(document_text=<summary>, num_hosts=2) to turn the summary into a dialogue between two speakers labelled clearly as either "Host:" or "Guest:" on each line.
   • Aim for 6–10 short lines total.
5. SPLIT the script into individual dialogue lines respecting original order.
6. For EACH line, do:
   • Identify the speaker: if the line starts with "Host", use the host_voice_id given by the user; if it starts with "Guest", use the guest_voice_id.
   • REMOVE the speaker label and trim whitespace.
   • CALL generate_audio_simple(text=<trimmed_line>, voice_id=<chosen_voice_id>) – keep the returned mp3 filename.
7. After all lines are voiced, CALL combine_mp3_files_for_podcast(mp3_files=<list_in_order>, output_filename="one_min_podcast.mp3") to merge them into the final show.
8. RETURN a JSON object that follows StructuredOutput exactly:
   • url – the original URL.
   • summary_text – the paragraph summary used for the show.
   • script_text – the full dialogue script (including speaker labels).
   • individual_audio_files – the ordered list of generated mp3 parts.
   • podcast_file – absolute path to the final merged mp3.

Strict rules:
• Never hallucinate tool names or parameters.
• Always check each tool call’s return for errors and stop early if any step fails.
• Keep the entire workflow within 1 minute of audio (roughly <= 900 characters total speech).
• Do NOT add extra commentary outside the StructuredOutput JSON.
'''

# ========== Tools definition ===========
from any_agent.config import MCPStdio

TOOLS = [
    extract_text_from_url,
    summarize_text_with_llm,
    generate_podcast_script_with_llm,
    combine_mp3_files_for_podcast,
    # ElevenLabs MCP server for TTS
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

def run_agent(url: str, host_voice_id: str, guest_voice_id: str):
    """Generate a one-minute podcast mp3 from a webpage, with separate Host and Guest voices produced via ElevenLabs, then merged into a single audio file."""
    input_prompt = f"Create a one-minute podcast from this article: {url}\nUse ElevenLabs voice ID {host_voice_id} for the Host and {guest_voice_id} for the Guest."
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
    Fire(run_agent)

