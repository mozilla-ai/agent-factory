## Setup & Run Instructions

1. **Clone your project and ensure Python 3.11 is installed.**

2. **Create a `.env` file in the project root with the following variables:**

```
# OpenAI key for the o3 model
OPENAI_API_KEY="your-openai-key"

# ElevenLabs text-to-speech key
ELEVENLABS_API_KEY="your-elevenlabs-key"
```

3. **Install dependencies and execute the agent (replace `<URL>` with the target webpage):**

```bash
uv run --with-requirements generated_workflows/latest/requirements.txt --python 3.11 \
  python generated_workflows/latest/agent.py --url "<URL>" --num_hosts 3
```

The script will output a JSON object containing the podcast script and the path/URL to the generated MP3 file. The full agent trace is stored at `generated_workflows/latest/agent_eval_trace.json` for later inspection.