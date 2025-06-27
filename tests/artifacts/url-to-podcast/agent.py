
# agent.py

# good to have
import os

# ALWAYS used
from pathlib import Path
from dotenv import load_dotenv
from any_agent import AgentConfig, AnyAgent, AgentRunError
from any_agent.config import MCPStdio
from pydantic import BaseModel, Field
from fire import Fire

# ADD BELOW HERE: tools made available by any-agent or agent-factory
# ADD BELOW HERE: tool imports
from tools.extract_text_from_url import extract_text_from_url
from tools.generate_podcast_script_with_llm import generate_podcast_script_with_llm
from tools.combine_mp3_files_for_podcast import combine_mp3_files_for_podcast

load_dotenv()

# ========== Structured output definition ==========
# ========== Structured output definition ==========
class StructuredOutput(BaseModel):
    url: str = Field(..., description="The original webpage URL.")
    num_hosts: int = Field(..., description="Number of hosts/speakers in the generated podcast.")
    script_text: str = Field(..., description="The full podcast script that was generated.")
    audio_file: str = Field(..., description="Path to the final MP3 podcast file.")

# ========== System (Multi-step) Instructions ===========
INSTRUCTIONS='''
You are an assistant that turns the content of a web page into an engaging multi-speaker podcast and returns a JSON summary of the process.  Follow these steps exactly and in order:

Step 1 – Extract page text
• Use the extract_text_from_url tool with the supplied URL.
• If the tool returns an error message, stop the workflow and return a StructuredOutput where script_text contains the error, audio_file is an empty string, and num_hosts is what the user requested.

Step 2 – Write the podcast script
• Call generate_podcast_script_with_llm with:
    – document_text = text from Step 1
    – num_hosts = value provided by the user (default 2)
• Ensure the script clearly labels speakers (e.g. “Host 1:”, “Host 2:” …).

Step 3 – Generate voiceover audio
• Invoke the generate_audio_script tool (from the ElevenLabs MCP) with the full script produced in Step 2.  Default voice settings are acceptable unless otherwise specified.
• The tool may return (a) a single MP3 file path or (b) a JSON / list of MP3 file paths.

Step 4 – (Optional) Combine multiple MP3 files
• If Step 3 returned more than one MP3 file, call combine_mp3_files_for_podcast with those files to create a single podcast MP3.  Use the resulting file as the final audio_file.
• If only one MP3 file was returned in Step 3, use it directly.

Step 5 – Final response
Return ONLY a JSON object that matches the StructuredOutput schema with fields:
  url – the original web address
  num_hosts – number of hosts requested
  script_text – the complete script produced in Step 2
  audio_file – absolute (or working-directory-relative) path to the final MP3 file.

Never reveal internal reasoning or tool call details.  Do not output anything except the JSON object.
'''

# ========== Tools definition ===========
# ========== Tools definition ==========
TOOLS = [
    extract_text_from_url,               # fetch the webpage text
    generate_podcast_script_with_llm,    # turn text into a dialog script
    combine_mp3_files_for_podcast,       # merge multiple mp3s if necessary
    MCPStdio(                            # text-to-speech via ElevenLabs
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
            "generate_audio_script",    # only tool we need from this MCP
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

def run_agent(url: str, num_hosts: int = 2):
    """Generate an engaging multi-speaker audio podcast (MP3) from the content of a given webpage URL and return structured details of the process."""
    input_prompt = f"Create an audio podcast with {num_hosts} hosts from the content of this webpage: {url}"
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

