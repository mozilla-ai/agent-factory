
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
from any_agent.config import MCPStdio
from tools.extract_text_from_url import extract_text_from_url
from tools.summarize_text_with_llm import summarize_text_with_llm
from tools.generate_podcast_script_with_llm import generate_podcast_script_with_llm
from tools.combine_mp3_files_for_podcast import combine_mp3_files_for_podcast

load_dotenv()

# ========== Structured output definition ==========
class StructuredOutput(BaseModel):
    final_podcast_mp3: str = Field(..., description="Relative path to the final, combined 1-minute podcast MP3 file.")
    script_text: str = Field(..., description="The full podcast script that was turned into audio.")
    mp3_list: list[str] = Field(..., description="Ordered list of intermediate MP3 file paths for each dialogue line.")

# ========== System (Multi-step) Instructions ===========
INSTRUCTIONS='''
You are an expert podcast-producer assistant.  Follow this concise multi-step workflow:
1. Input is a single web URL.
2. Use extract_text_from_url to fetch and clean all readable text.  If the tool returns an error, STOP and respond with a clear error message.
3. Pass the extracted text to summarize_text_with_llm asking for a ~150-word concise summary (suitable for a 1-minute show).
4. Feed the summary to generate_podcast_script_with_llm with num_hosts=2.  Instruct it to:   
   • create a lively dialogue labelled exactly "Host:" and "Guest:"   
   • keep total spoken words ≈ 150–180 (≈60 seconds)   
   • alternate turns starting with Host and ending with Host or Guest outro.
5. Split the script into ordered dialogue lines.  For each line:   
   • remove the "Host:"/"Guest:" label for cleaner audio   
   • call generate_audio_simple (ElevenLabs) with that text.  Collect the returned mp3 filepath in order.   
6. After all lines are voiced, call combine_mp3_files_for_podcast with the list of mp3 files (keep order) and output_filename="podcast_final.mp3".  The tool returns the combined file path.
7. Respond with JSON structured as StructuredOutput (defined below).

Always respect the order of steps, use the specified tools only once per step, and keep all intermediate and final files in relative paths.  Do NOT embed raw binary data in the output.  Do not hallucinate file paths.  If any step fails, return a JSON object with an explanation in the final_podcast_mp3 field and leave mp3_lists empty.
'''

# ========== Tools definition ===========
from any_agent.config import MCPStdio
from tools.extract_text_from_url import extract_text_from_url
from tools.summarize_text_with_llm import summarize_text_with_llm
from tools.generate_podcast_script_with_llm import generate_podcast_script_with_llm
from tools.combine_mp3_files_for_podcast import combine_mp3_files_for_podcast

TOOLS = [
    extract_text_from_url,
    summarize_text_with_llm,
    generate_podcast_script_with_llm,
    combine_mp3_files_for_podcast,
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

def run_agent(url: str):
    """Generate a 1-minute two-speaker podcast from a webpage and output the final MP3 file path plus details."""
    input_prompt = f"Create a concise one-minute podcast based on the content at: {url}"
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

