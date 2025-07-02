
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
from any_agent.config import MCPStdio

load_dotenv()

# ========== Structured output definition ==========
class StructuredOutput(BaseModel):
    url: str = Field(..., description="The original webpage URL provided by the user.")
    script: str = Field(..., description="The generated 1-minute podcast script featuring Host and Guest lines.")
    audio_files: list[str] = Field(..., description="Ordered list of individual MP3 file paths for each dialogue line.")
    final_podcast_path: str = Field(..., description="Absolute path to the combined final podcast MP3 file.")


# ========== System (Multi-step) Instructions ===========
INSTRUCTIONS='''
You are an autonomous agent that converts the content of a webpage into a short (≈1-minute) podcast featuring a dialogue between a Host and a Guest.  Strictly follow the workflow below and only use the provided tools.

Step 1 – Extract content
• Receive a URL in the user prompt.
• Call extract_text_from_url on that URL to obtain clean, human-readable text.
• If the tool returns an error string beginning with “Error”, try once more with the same URL; if it still fails, stop and explain the failure in the final output.

Step 2 – Draft a 1-minute dialogue script
• Summarise the extracted text into a conversational podcast script that can be spoken in ~60 seconds (≈150–180 words).
• Use generate_podcast_script_with_llm with num_hosts=2.
• Alternate lines clearly labelled “Host:” and “Guest:”. Keep sentences short, engaging and faithful to the source.

Step 3 – Generate individual MP3 clips
• Split the script into separate lines by speaker.
• For each line, call generate_audio_script via the ElevenLabs MCP server.  Provide a JSON string in the form:
  {
    "script": [
      {"text": "<line text without label>", "actor": "Host" | "Guest"}
    ]
  }
• Capture the returned path to the generated MP3 file (the MCP tool returns a local path on success).
• Maintain an ordered list (audio_files) of all generated MP3 clips.
• If generate_audio_script returns an error string beginning with “Error”, retry once; upon repeated failure, skip that line and note the omission in the script.

Step 4 – Merge dialogue clips
• Call combine_mp3_files_for_podcast with audio_files and output_filename="podcast.mp3".
• Record the absolute path returned (final_podcast_path).  If the tool returns an error string beginning with “Error”, retry once; otherwise halt with failure information.

Step 5 – Structured JSON output
Return a StructuredOutput object with the following fields:
• url – original URL
• script – full podcast script produced in Step 2
• audio_files – ordered list of individual MP3 paths from Step 3
• final_podcast_path – path to the combined podcast MP3 from Step 4

General rules
• Keep the total number of agent turns ≤ 20.
• Do not embed or print raw binary audio data.
• Never invent tool outputs; always read and use the actual return values.
• Stay concise yet complete in the script, aiming for ≈1-minute total runtime.

'''

# ========== Tools definition ===========
# ========= Tools definition =========
from any_agent.config import MCPStdio

TOOLS = [
    extract_text_from_url,            # Fetch & clean webpage text
    generate_podcast_script_with_llm, # Create the dialogue script
    combine_mp3_files_for_podcast,    # Merge MP3 clips into one file
    MCPStdio(                         # ElevenLabs text-to-speech capabilities
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
            "generate_audio_script",   # Generate voice clip from a single line
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

def run_agent(url: str):
    """Given a webpage URL, create a 1-minute two-person podcast episode, convert each dialogue line to speech with ElevenLabs, merge the clips, and return paths to all generated audio files."""
    input_prompt = f"Create a 1-minute podcast featuring a Host–Guest dialogue based on the contents of this URL: {url}"
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

