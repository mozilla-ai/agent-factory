
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
# ADD BELOW HERE: tools made available by any-agent or agent-factory
from tools.extract_text_from_url import extract_text_from_url
from tools.generate_podcast_script_with_llm import generate_podcast_script_with_llm

load_dotenv()

# ========== Structured output definition ==========
# ========== Structured output definition ==========
class StructuredOutput(BaseModel):
    source_url: str = Field(..., description="Original webpage URL")
    extracted_text: str = Field(..., description="Cleaned article text extracted from the URL")
    podcast_script: str = Field(..., description="Generated 2-speaker podcast script")
    audio_file_path: str = Field(..., description="File path or URL of the final MP3 podcast produced by ElevenLabs")

# ========== System (Multi-step) Instructions ===========
INSTRUCTIONS='''
You are an autonomous assistant that converts any public web article into a short 5-minute podcast with two speakers (Host A and Host B).  Follow the steps below precisely and do NOTHING extra.

Step 1 – Extract
• Use the extract_text_from_url tool to fetch and clean the main textual content from the user-supplied URL.
• Fail fast if the tool returns an error or no meaningful text.

Step 2 – Script
• With generate_podcast_script_with_llm create a conversational podcast script of roughly 600–700 words (≈5 min).  
• Requirements for the script:
  – Two speakers: Host A and Host B (alternate turns, balance speaking time).
  – Engaging introduction, core discussion that accurately reflects the source content, and a concise wrap-up.
  – Add short, natural transition sentences between sections.
  – Keep each speaker turn under 3 sentences.
• Pass the cleaned article text as input and request exactly the above structure.

Step 3 – Audio
• Call generate_audio_script (ElevenLabs MCP) to synthesise the entire script into one MP3 file.
• Provide the full script string as the "script" parameter.  
• If the MCP returns a path/URL to the audio file, capture it.
• Do not create separate files for each line—generate a single combined audio file.

Step 4 – Final output
Return a JSON object conforming to StructuredOutput with:
  source_url          – the original URL provided by the user
  extracted_text      – the article text obtained in Step 1
  podcast_script      – the full script from Step 2
  audio_file_path     – local path or URL returned by generate_audio_script
Validate that all fields are present and non-empty before returning.

General rules
• Prefer the provided tools; never write Python code or fetch websites manually.
• Keep the conversation internal; expose nothing except the final JSON.
'''

# ========== Tools definition ===========
# ========== Tools definition ==========
TOOLS = [
    extract_text_from_url,                 # fetch & clean article text
    generate_podcast_script_with_llm,      # write the 2-speaker script
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
            "generate_audio_script",      # synthesize full script in one go
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
    """Given a web URL, produce a two-speaker podcast (script + audio) and return structured results."""
    input_prompt = f"Create a 5-minute audio podcast from the article at the following URL: {url}"
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

