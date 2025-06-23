### Setup instructions

1. **Clone / download the project** and ensure you have Python **3.11** installed.

2. **Create a `.env` file** in the project root with the following variables (obtain keys from your ElevenLabs dashboard):

```
OPENAI_API_KEY=your_openai_key_here
ELEVENLABS_API_KEY=your_elevenlabs_api_key_here
```

3. **Install dependencies and run the agent** (Linux / macOS example):

```bash
uv run --with-requirements generated_workflows/latest/requirements.txt --python 3.11 \
    python generated_workflows/latest/agent.py --url "https://example.com/some-article" --num_hosts 2
```

> **Note**: `ffmpeg` must be installed and available in your system `PATH` for audio concatenation.
