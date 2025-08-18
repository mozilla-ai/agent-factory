# PodCraft – Webpage-to-Podcast Agent

PodCraft turns any webpage into a short dialog-style podcast by extracting its text, writing a dialog script, converting each line to speech with ElevenLabs voices, and merging the audio into a single mp3.

## Prerequisites

- **uv**
- **mcpd**

### Install uv

- macOS / Linux
  ```bash
  curl -LsSf https://astral.sh/uv/install.sh | sh
  ```
- Windows PowerShell
  ```powershell
  powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
  ```

### Install mcpd

Follow the official guide: https://mozilla-ai.github.io/mcpd/installation/

## Configuration

Create a `.env` file at the project root containing:

```bash
OPENAI_API_KEY=your-openai-key
ELEVENLABS_API_KEY=your-elevenlabs-key
```

## Run the Agent

1. Start the mcpd daemon so the ElevenLabs MCP server is available:
   ```bash
   mcpd daemon --log-level=DEBUG --log-path=$(pwd)/mcpd.log --dev --runtime-file secrets.dev.toml
   ```
2. Run the agent:
   ```bash
   uv run --with-requirements requirements.txt --python 3.13 python agent.py --url "https://example.com"
   ```

The generated podcast will be saved to `/tmp/podcast.mp3`.
