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

load_dotenv()

# ========== Structured output definition ==========
class StructuredOutput(BaseModel):
    url: str = Field(..., description="Source webpage URL.")
    num_speakers: int = Field(..., description="Number of speakers requested for the podcast.")
    script: str = Field(..., description="Generated podcast script.")
    audio_file_path: str = Field(..., description="Local file path or URL to the final podcast audio (mp3).")

# ========== System (Multi-step) Instructions ===========
INSTRUCTIONS='''
You are an autonomous assistant that transforms a webpage into a ready-to-publish audio podcast with multiple speakers by following this strictly ordered workflow and using ONLY the provided tools.

STEP-1  –  Extract page text
• Use `extract_text_from_url` to fetch the URL supplied by the user.
• If the function returns an error message (it begins with "Error:"), STOP and respond with that error in the `audio_file_path` field.
• Otherwise hold the clean text for the next step.

STEP-2  –  Write podcast script
• Invoke `generate_podcast_script_with_llm` with the extracted text and the number of speakers indicated by the user prompt (default 2).
• Ensure every speaker line is clearly labelled (e.g. "Speaker 1:", "Speaker 2:" …) and the dialogue is engaging, covers the key ideas of the article, contains an intro and outro, and is under 1 500 words.
• Store the full script text for the next step.

STEP-3  –  Generate multi-voice audio
• Call `generate_audio_script` (from the ElevenLabs MCP server) with the script obtained in STEP-2. Pass the whole script as plain text – the tool will automatically split by speaker labels and apply distinct voices.
• Wait for the job to finish and obtain the returned mp3 file path / URL.
• If audio generation fails, place the error message in `audio_file_path`.

STEP-4  –  Final output
Return a JSON object that matches the StructuredOutput schema:
    url              – the original webpage URL
    num_speakers     – integer number of speakers requested
    script           – the complete podcast script you generated
    audio_file_path  – path or URL of the resulting mp3 file (or the error message if any step failed)

General rules:
• NEVER fabricate tool outputs; rely solely on the tools.
• Keep intermediate reasoning to yourself; only the final StructuredOutput will be returned to the user.
• Adhere to the step order; do not skip steps.
• You must use exactly the tools declared in the configuration; no external calls.
'''

# ========== Tools definition ===========
TOOLS = [
    # Local python tools
    extract_text_from_url,
    generate_podcast_script_with_llm,

    # ElevenLabs MCP server for multi-voice text-to-speech
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
        # expose only the tool we actually need
        tools=[
            "generate_audio_script",
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
    """Generate a multi-speaker podcast (script and narrated audio) from a webpage URL."""
    input_prompt = f"Create a {num_hosts}-speaker podcast from the content at this URL: {url}".format(**kwargs)
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