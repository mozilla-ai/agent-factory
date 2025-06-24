# agent.py

import os
from dotenv import load_dotenv
from any_agent import AgentConfig, AnyAgent, AgentRunError
from any_agent.config import MCPStdio
from pydantic import BaseModel, Field
from fire import Fire

# ---- Local python-function tools ----
from tools.extract_text_from_url import extract_text_from_url
from tools.generate_podcast_script_with_llm import generate_podcast_script_with_llm

# ---- Load environment variables ----
load_dotenv()

# ========== Structured output definition ==========
class StructuredOutput(BaseModel):
    url: str = Field(..., description="The original webpage URL used as source material.")
    script: str = Field(..., description="The complete podcast script with speaker labels.")
    audio_file: str = Field(..., description="Filesystem path or URL to the generated podcast MP3 file.")

# ========== System (Multi-step) Instructions ==========
INSTRUCTIONS = """
You are an assistant that converts webpage content into a narrated multi-speaker podcast.  
Follow this strict 3-step workflow and ONLY use the designated tools to accomplish each step.

STEP 1 – Extract Source Text  
• Use the `extract_text_from_url` tool to fetch and extract the primary textual content from the provided `url`.  
• Strip boiler-plate (menus, navigation, ads) wherever possible. Store the result as **page_text**.

STEP 2 – Write Podcast Script  
• Invoke `generate_podcast_script_with_llm` giving it **page_text** and the requested `num_hosts`.  
• The script MUST clearly label each host/speaker (e.g., "Host 1:", "Host 2:").  
• Ensure the dialogue covers the important points in an engaging conversational style. Save as **podcast_script**.

STEP 3 – Produce Audio  
• Pass **podcast_script** to the `generate_audio_script` tool (from the ElevenLabs MCP server).  
• A single MP3 file containing the full conversation should be generated. Capture the returned file path or URL as **audio_path**.

FINAL RESPONSE  
Return a JSON object using the provided `StructuredOutput` schema with:  
• url – the original webpage URL  
• script – the full **podcast_script**  
• audio_file – **audio_path** returned by the TTS tool
"""

# ========== Tools definition ==========
TOOLS = [
    # Local Python-function tools
    extract_text_from_url,
    generate_podcast_script_with_llm,
    # ElevenLabs MCP server – we only need the generate_audio_script tool
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

# ========================= Runner =========================

def run_agent(url: str, num_hosts: int = 2):
    """Create a multi-speaker audio podcast from the content of the given webpage URL."""
    input_prompt = (
        "Create an audio podcast from the webpage at {url}. "
        "The podcast should feature {num_hosts} distinct hosts.".format(url=url, num_hosts=num_hosts)
    )

    try:
        agent_trace = agent.run(prompt=input_prompt, max_turns=20)
    except AgentRunError as e:
        agent_trace = e.trace
        print(f"Agent execution failed: {str(e)}")
        print("Retrieved partial agent trace…")

    # Persist trace for later evaluation
    with open("generated_workflows/latest/agent_eval_trace.json", "w", encoding="utf-8") as f:
        f.write(agent_trace.model_dump_json(indent=2))

    return agent_trace.final_output


if __name__ == "__main__":
    Fire(run_agent)