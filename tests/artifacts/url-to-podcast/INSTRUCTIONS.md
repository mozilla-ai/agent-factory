## Setup & Run Instructions

1. **Clone the repository / place the files** so that `agent.py`, the `tools/` directory and `generated_workflows/latest/` directory are in the same root.

2. **Create a `.env` file** in the project root with these environment variables:

```dotenv
# OpenAI model access
OPENAI_API_KEY=your_openai_key

# ElevenLabs text-to-speech
ELEVENLABS_API_KEY=your_elevenlabs_key
```

*(If you prefer specific ElevenLabs voices, pass them via the CLI when running the agent.)*

3. **Install dependencies & run the agent** (requires Python 3.11):

```bash
uv run --with-requirements generated_workflows/latest/requirements.txt --python 3.11 \
  python generated_workflows/latest/agent.py --url "https://example.com/interesting-article" --voice_ids "voiceId1,voiceId2"
```

The script will:
1. Extract the article text.  
2. Write a two-host podcast script.  
3. Synthesise the dialogue using ElevenLabs voices.  
4. Merge the audio into `podcast_episode.mp3` in the current directory.  
5. Save an execution trace at `generated_workflows/latest/agent_eval_trace.json` for evaluation.
