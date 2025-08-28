
# agent.py

# Always used imports
import json  # noqa: I001
import os
import sys
from pathlib import Path

from any_agent import AgentConfig, AgentRunError, AnyAgent
from dotenv import load_dotenv
from fire import Fire
from mcpd import McpdClient, McpdError
from pydantic import BaseModel, Field

# ADD BELOW HERE: tools made available by any-agent or agent-factory
from tools.visit_webpage import visit_webpage
from tools.extract_text_from_markdown_or_html import extract_text_from_markdown_or_html
from tools.generate_podcast_script_with_llm import generate_podcast_script_with_llm
from tools.combine_mp3_files_for_podcast import combine_mp3_files_for_podcast

load_dotenv()

# Connect to mcpd daemon for accessing available tools
MCPD_ENDPOINT = os.getenv("MCPD_ADDR", "http://localhost:8090")
MCPD_API_KEY = os.getenv("MCPD_API_KEY", None)

# ========== Structured output definition ==========
class StructuredOutput(BaseModel):
    """Schema for the agent's final output."""

    url: str = Field(..., description="Original webpage URL supplied by user.")
    script_turns: int = Field(..., description="Total number of dialogue turns in the generated script.")
    segment_files: list[str] = Field(
        ..., description="Absolute paths of individual MP3 segment files for each dialogue turn, ordered."
    )
    final_podcast_path: str = Field(..., description="Absolute path of the combined podcast MP3 file saved in /tmp.")
    error: str | None = Field(None, description="Error message, if any step fails.")

# ========== System (Multi-step) Instructions ===========
INSTRUCTIONS='''
You are PodcastCreatorBot, an AI assistant that takes a webpage URL and produces a concise, engaging podcast dialogue (≤16 turns) between two speakers, then converts it to a single MP3 file.

Follow this strict multi-step workflow and ONLY use the provided tools when required:

Step 1 – Fetch & Clean Content
• Use visit_webpage(url) to download the page as markdown.
• Immediately pass the markdown into extract_text_from_markdown_or_html(content) to obtain clean plain text.
• Keep roughly the first 1 000 words (enough context, but short).

Step 2 – Draft Podcast Script
• Choose speaker names: "Alex (Host)" and "Jordan (Guest)".
• Call generate_podcast_script_with_llm(document_text=text, num_hosts=2, host_names=["Alex","Jordan"], turns=16).
• The tool returns a JSON list where each item maps speaker → utterance.

Step 3 – Text-to-Speech for Each Turn
• For every item in the JSON list, determine the speaker:
  – Alex → ElevenLabs voice "Rachel"
  – Jordan → ElevenLabs voice "Drew"
• Invoke text_to_speech(text=<utterance>, voice_name=<voice>, output_dir="/tmp") for each line, in the original order, and store the returned mp3 filenames in an array.

Step 4 – Combine Audio
• After generating all segment files, call combine_mp3_files_for_podcast(mp3_files=<array>, output_filename="podcast_final.mp3", output_dir="/tmp").
• Record the absolute path returned (e.g. "/tmp/podcast_final.mp3").

Step 5 – Final Structured Response
Return a StructuredOutput JSON object with:
  url – the original URL
  script_turns – total number of dialogue turns created
  segment_files – list of individual mp3 segment file paths
  final_podcast_path – path of the combined MP3 file in /tmp

General Rules
• Keep dialogue natural, informative & faithful to webpage content—no hallucination.
• Ensure total turns ≤16.
• Always save ALL audio files in /tmp.
• If any step fails, STOP and reply with an error message inside StructuredOutput.error.
• Be concise in tool arguments and ALWAYS include necessary parameters (voice_name and output_dir for text_to_speech).
• Never print raw tool outputs—only pass them between steps internally.
'''

# ========== Tools definition ===========
TOOLS = [
    visit_webpage,
    extract_text_from_markdown_or_html,
    generate_podcast_script_with_llm,
    combine_mp3_files_for_podcast,
]

try:
    mcpd_client = McpdClient(api_endpoint=MCPD_ENDPOINT, api_key=MCPD_API_KEY)
    mcp_server_tools = mcpd_client.agent_tools()
    if not mcp_server_tools:
        print("No tools found via mcpd.")
    TOOLS.extend(mcp_server_tools)
except McpdError as e:
    print(
        f"Error connecting to mcpd: {e}. If the agent doesn't use any MCP servers you can safely ignore this error",
        file=sys.stderr
    )

# ========== Running the agent via CLI ===========
agent = AnyAgent.create(
    "openai",
    AgentConfig(
        model_id="o3",
        instructions=INSTRUCTIONS,
        tools=TOOLS,
        output_type=StructuredOutput,  # name of the Pydantic v2 model defined above
        model_args={"tool_choice": "auto"},
    ),
)


def main(url: str):
    """Generate a short (≤16-turn) two-speaker podcast from a webpage URL, convert dialogue to speech with ElevenLabs voices, and output a single MP3 saved in /tmp."""
    input_prompt = f"Create a concise podcast from the following webpage: {url}"
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
            print(cost_msg)
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

    with output_path.open("w", encoding="utf-8") as f:
        f.write(json.dumps(trace_data, indent=2))

    return agent_trace.final_output


if __name__ == "__main__":
    Fire(main)
