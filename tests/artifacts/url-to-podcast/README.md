# Web-to-Podcast Generator Agent

This agent converts the text content of any webpage into a short (≤ 16-turn) podcast. It writes a dialogue script, generates per-turn speech with ElevenLabs voices, and merges the segments into a single MP3 saved in `/tmp/podcast.mp3`.

# Prerequisites

- uv
- mcpd

## Install uv

- **macOS / Linux**
    ```bash
    curl -LsSf https://astral.sh/uv/install.sh | sh
    ```
- **Windows PowerShell**
    ```powershell
    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
    ```

## Install mcpd

Follow the mcpd installation instructions in the official documentation: https://mozilla-ai.github.io/mcpd/installation/

# Configuration

Create a `.env` file in the project root and add the required environment variables, for example:

```
OPENAI_API_KEY=your-openai-key
ELEVENLABS_API_KEY=your-elevenlabs-key
```

# Run the Agent

1. Export your .env variables and start the MCP daemon:

```bash
export $(cat .env | xargs) && mcpd daemon --log-level=DEBUG --log-path=$(pwd)/mcpd.log --dev --runtime-file secrets.prod.toml
```

2. Run the agent:

```bash
uv run --with-requirements requirements.txt --python 3.13 python agent.py --url "https://example.com/article"
```

The generated podcast will be available at `/tmp/podcast.mp3`. Enjoy!
