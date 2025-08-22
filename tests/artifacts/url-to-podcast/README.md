# URL-to-Podcast Generator

Creates a short (≤16 turns) podcast MP3 from any webpage: it extracts the article, writes a host/guest script, converts each turn to speech with ElevenLabs voices, and merges everything into a single MP3 stored in `/tmp/podcast.mp3`.

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

Set the environment variables in the `.env` file that has been created for you. Add other environment variables as needed, for example, environment variables for your LLM provider.

Add `ELEVENLABS_API_KEY` to the `.env` file so the ElevenLabs MCP server can authenticate.

# Run the Agent

1. Run the mcpd daemon:
```bash
mcpd daemon --log-level=DEBUG --log-path=$(pwd)/mcpd.log --dev --runtime-file secrets.prod.toml
```
2. Run the agent:
```bash
uv run --with-requirements requirements.txt --python 3.13 python agent.py --url "https://example.com/article"
```
