# URL-to-Podcast Agent

Turn any webpage into a short, dialogue-style podcast and save the final MP3 in `/tmp`.

## Prerequisites

- uv
- mcpd

### Install uv (package manager)

- **macOS / Linux**
    ```bash
    curl -LsSf https://astral.sh/uv/install.sh | sh
    ```
- **Windows PowerShell**
    ```powershell
    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
    ```

### Install mcpd

Follow the official instructions: https://mozilla-ai.github.io/mcpd/installation/

## Configuration

Create a `.env` file in the project root and add:

```
OPENAI_API_KEY=your-openai-key
ELEVENLABS_API_KEY=your-elevenlabs-key
```

## Run the Agent

1. Start the mcpd daemon (needed for ElevenLabs MCP server):
   ```bash
   mcpd daemon --log-level=DEBUG --log-path=$(pwd)/mcpd.log --dev
   ```
2. Execute the agent:
   ```bash
   uv run --with-requirements requirements.txt --python 3.13 python agent.py --url "https://example.com"
   ```

The merged podcast will be saved to `/tmp/podcast.mp3`, and a full execution trace to `agent_eval_trace.json`.
