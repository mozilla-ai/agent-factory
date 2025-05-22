import os

from any_agent import AgentConfig, AnyAgent
from any_agent.config import MCPStdio
from any_agent.tools import search_web
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from tools.combine_mp3_files_for_podcast import combine_mp3_files_for_podcast
from tools.generate_podcast_script_with_llm import generate_podcast_script_with_llm

load_dotenv()

# --- Pydantic Models ---


class PodcastOutput(BaseModel):
    topic: str = Field(..., description="The topic requested by the user.")
    script: str = Field(..., description="The full 1-minute two-speaker script generated for the podcast.")
    mp3_files: list[str] = Field(
        ..., description="Ordered MP3 audio file paths for all podcast speaker audio segments (before combining)."
    )
    final_podcast_mp3: str = Field(..., description="Path to the final combined podcast MP3 file.")
    used_voices: list[str] = Field(
        ..., description="Human-readable names or IDs of voices used for Speaker 1 and Speaker 2."
    )


# --- Agent System Instructions ---

INSTRUCTIONS = """
You are a podcast creation assistant. When given a topic, follow these steps:

1. Briefly research the topic. Gather a concise overview and the most interesting points, enough for a roughly one-minute podcast episode.
2. Generate a natural, engaging script for a two-speaker podcast (Speaker A and Speaker B). Each speaker should have distinct, alternating lines but roughly equal speaking time. Cover all key points fitting within a 1-minute time window (approx. 140-180 words total). Start with an intro, include at least one back-and-forth exchange, and finish with an outro.
3. For each speaker, convert only their lines into separate MP3 audio files using ElevenLabs text-to-speech. Use a distinct voice for each speaker. Save the audio segments in order.
4. Combine all generated MP3 files into a single podcast MP3 using the available tool.
5. Return a structured result containing the original topic, the final script text, the list of generated mp3 segment files, the final podcast mp3 path, and the voices used for Speaker A and Speaker B.

When running tools, provide each speaker line as input separately for TTS to ensure realistic speaker alternation.
"""

# --- Agent Configuration ---

agent = AnyAgent.create(
    "openai",
    AgentConfig(
        model_id="gpt-4.1",
        instructions=INSTRUCTIONS,
        tools=[
            search_web,
            generate_podcast_script_with_llm,
            combine_mp3_files_for_podcast,
            MCPStdio(
                command="uvx",
                args=["elevenlabs-mcp"],
                env={
                    "ELEVENLABS_API_KEY": os.getenv("ELEVENLABS_API_KEY"),
                },
                tools=["text_to_speech"],
            ),
        ],
        agent_args={"output_type": PodcastOutput},
    ),
)

# --- Entry Point ---

if __name__ == "__main__":
    import sys

    print("Enter a one-sentence topic for your podcast, for example: 'AI and the Future of Work'")
    user_topic = input("Podcast topic: ").strip()
    if not user_topic:
        print("No topic entered. Exiting.")
        sys.exit(1)
    prompt = (
        f"Create a high-quality two-speaker podcast episode on the following topic: '{user_topic}'. "
        f"Follow all system instructions step by step. Ensure that each speaker's lines are processed in alternating order via text-to-speech and the final audio files are combined."
    )
    trace = agent.run(prompt=prompt)
    print("Structured Output:\n")
    print(trace.final_output)
    print("\nPodcast generation complete.")
