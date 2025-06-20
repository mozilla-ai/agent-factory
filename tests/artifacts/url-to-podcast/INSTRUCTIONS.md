## Setup & Run Instructions

1. **Create a virtual environment (optional but recommended)**

```bash
python3.11 -m venv .venv
source .venv/bin/activate
```

2. **Create a `.env` file** in the project root and add the following keys:

```env
# OpenAI / Azure-OpenAI key for any-agent to call the LLM
OPENAI_API_KEY=YOUR_OPENAI_KEY_HERE

# ElevenLabs key for text-to-speech
ELEVENLABS_API_KEY=YOUR_ELEVENLABS_KEY_HERE
```

3. **Install dependencies & run** using `uv` (ensures deterministic builds):

```bash
uv run --with-requirements generated_workflows/latest/requirements.txt --python 3.11 \
  python generated_workflows/latest/agent.py --url "https://example.com" --num_speakers 3
```

Replace the URL with any article you want converted into a podcast.


