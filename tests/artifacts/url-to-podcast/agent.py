# agent.py

# good to have
import os

# ALWAYS used
from dotenv import load_dotenv
from any_agent import AgentConfig, AnyAgent
from any_agent.config import MCPStdio
from pydantic import BaseModel, Field
from fire import Fire

# ADD BELOW HERE: tools made available by any-agent or agent-factory
from tools.extract_text_from_url import extract_text_from_url
from tools.generate_podcast_script_with_llm import generate_podcast_script_with_llm
from any_agent.tools import visit_webpage  # Not used but kept if needed later

load_dotenv()

# ========== Structured output definition ==========
# ========== Structured output definition ==========
class StructuredOutput(BaseModel):
    url: str = Field(..., description="Original webpage URL used as input.")
    podcast_script: str = Field(..., description="The complete podcast script with speaker turns.")
    audio_file_path: str = Field(..., description="Local filesystem path of the generated multi-speaker audio mp3 file.")

# ========== System (Multi-step) Instructions ===========
INSTRUCTIONS='''
You are an assistant that creates an audio podcast with multiple speakers from the content of a webpage. Follow this concise multi-step workflow and use the provided tools exactly as instructed. Always think step-by-step and only proceed to the next step when the previous one is complete.

STEP 1 – EXTRACT SOURCE TEXT
• Input: the user supplies a single webpage URL.
• Tool: call extract_text_from_url with the provided URL.
• Output variable: source_text – the main textual content of the page (exclude navigation, ads, comments, footers).

STEP 2 – WRITE PODCAST SCRIPT
• Tool: call generate_podcast_script_with_llm.
    – Arguments: text=source_text, num_hosts=2 (at least two distinct speakers), style="conversational, engaging, informative".
• The tool returns podcast_script (string). Make sure each speaker turn begins with the speaker name followed by a colon (e.g., "Host 1:"). Keep total length under 1 500 words.

STEP 3 – GENERATE MULTI-SPEAKER AUDIO
• Convert podcast_script into JSON compatible with ElevenLabs generate_audio_script tool.
    Format: {"script":[{"text":"...","actor":"Host 1"}, {"text":"...","actor":"Host 2"}, …]}
• Tool: call generate_audio_script from the ElevenLabs MCP server.
• Capture the returned local file path of the generated mp3 audio as audio_file_path.

STEP 4 – OUTPUT
Return a JSON object that matches the StructuredOutput schema with fields:
    url – the original webpage URL provided by the user
    podcast_script – the full script generated in STEP 2
    audio_file_path – the path to the final multi-speaker mp3 audio returned in STEP 3

General rules:
• Use only the specified tools; do not rely on hidden knowledge.
• If any tool fails, explain the error in the corresponding output field and stop.
• Respond only with data that fits the StructuredOutput model.
'''

# ========== Tools definition ===========
# ========== Tools definition ==========
TOOLS = [
    extract_text_from_url,            # Fetch & extract webpage text
    generate_podcast_script_with_llm, # Convert text to multi-speaker script
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
            "generate_audio_script",  # Text-to-speech with multiple actors
        ],
    ),
]


agent = AnyAgent.create(
    "openai",
    AgentConfig(
        model_id="o3",
        instructions=INSTRUCTIONS,
        tools=TOOLS,
        agent_args={"output_type": StructuredOutput},
        model_args={"tool_choice": "required"},
    ),
)

def run_agent(url: str):
    """Generate a multi-speaker podcast from the textual content of a webpage and return structured data with the script and audio file path."""
    input_prompt = f"Create an audio podcast with multiple speakers from this webpage: {url}"
    agent_trace = agent.run(prompt=input_prompt, max_turns=25)
    with open("generated_workflows/latest/agent_eval_trace.json", "w", encoding="utf-8") as f:
        f.write(agent_trace.model_dump_json(indent=2))
    return agent_trace.final_output

if __name__ == "__main__":
    Fire(run_agent)