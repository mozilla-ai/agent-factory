
# agent.py

# good to have
import os

# ALWAYS used
from dotenv import load_dotenv
from any_agent import AgentConfig, AnyAgent, AgentRunError
from any_agent.config import MCPStdio
from pydantic import BaseModel, Field
from fire import Fire

# ADD BELOW HERE: tools made available by any-agent or agent-factory
from tools.extract_text_from_url import extract_text_from_url
from tools.generate_podcast_script_with_llm import generate_podcast_script_with_llm
from tools.combine_mp3_files_for_podcast import combine_mp3_files_for_podcast

load_dotenv()

# ========== Structured output definition ==========
class StructuredOutput(BaseModel):
    url: str = Field(..., description="Original webpage URL")
    num_speakers: int = Field(..., description="Number of podcast speakers/hosts")
    script_text: str = Field(..., description="Full podcast script generated from the webpage text")
    audio_file_path: str = Field(..., description="Filesystem path to the final combined MP3 podcast file")

# ========== System (Multi-step) Instructions ===========
INSTRUCTIONS='''
You are an expert podcast-producer assistant.  Follow this concise, 4-step workflow every time:
1. Text extraction – Given a webpage URL, call `extract_text_from_url` to retrieve the main readable text (ignore navigation, ads, code blocks, non-content elements).  Save the result in a variable `webpage_text`.  If extraction fails, stop and reply with an error message.
2. Script writing – Call `generate_podcast_script_with_llm` with `webpage_text` and the desired **number of speakers** (provided in the user prompt) to create an engaging podcast script.  The script MUST:
   • alternate among the speakers (e.g. "Host 1:", "Host 2:" …) 
   • faithfully cover the key ideas of the page without hallucination
   • be returned as plain text suitable for TTS or as a JSON list of segments (your choice)
   Save the result as `podcast_script`.
3. Audio generation – Pass `podcast_script` to the ElevenLabs MCP tool `generate_audio_script` to synthesize voices.  Supply either the plain script string or a JSON array where each element contains `text` and an `actor`/`voice_id`.  Capture the file path(s) (one or many) returned in a variable `audio_paths`.
4. Assembly & output – If `audio_paths` contains more than one mp3, merge them into a single file using `combine_mp3_files_for_podcast`; otherwise use the single file directly.  Name the final file `podcast_<timestamp>.mp3`.  Return a structured JSON object with:
   • url – the original webpage URL
   • num_speakers – the integer number of speakers used
   • script_text – the full podcast script you generated
   • audio_file_path – path to the final merged mp3

General rules:
• Use the tools exactly as specified.
• Stick to the 4 steps; do not skip or reorder them.
• Never include tool call arguments in the final answer – only the required structured JSON.
• If any step fails, give a clear error inside the structured output and leave the other fields empty.
'''

# ========== Tools definition ===========
# ========== Tools definition ===========
from tools.extract_text_from_url import extract_text_from_url
from tools.generate_podcast_script_with_llm import generate_podcast_script_with_llm
from tools.combine_mp3_files_for_podcast import combine_mp3_files_for_podcast

TOOLS = [
    extract_text_from_url,                 # fetch webpage text
    generate_podcast_script_with_llm,      # draft multi-speaker script
    combine_mp3_files_for_podcast,         # merge mp3s if needed
    MCPStdio(                              # ElevenLabs text-to-speech
        command="docker",
        args=[
            "run", "-i", "--rm",
            "-e", "ELEVENLABS_API_KEY",
            "mcp/elevenlabs",
        ],
        env={
            "ELEVENLABS_API_KEY": os.getenv("ELEVENLABS_API_KEY"),
        },
        tools=[
            "generate_audio_script",      # only tool we actually need
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

def run_agent(url: str, num_speakers: int = 2):
    """Generate a multi-speaker podcast from a webpage: extract the article, write a conversational script, convert it to speech with multiple voices, and return the mp3 location."""
    input_prompt = f"Create an audio podcast with {num_speakers} speakers from the content of this webpage: {url}"
    try:
        agent_trace = agent.run(prompt=input_prompt, max_turns=20)
    except AgentRunError as e:
        agent_trace = e.trace
        print(f"Agent execution failed: {str(e)}")
        print("Retrieved partial agent trace...")
    with open("generated_workflows/latest/agent_eval_trace.json", "w", encoding="utf-8") as f:
        f.write(agent_trace.model_dump_json(indent=2))
    return agent_trace.final_output

if __name__ == "__main__":
    Fire(run_agent)

