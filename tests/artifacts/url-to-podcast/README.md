# Web-to-Podcast Agent

Turns any web page into a short, two-speaker podcast, voices it with ElevenLabs, and produces a final MP3 saved in `/tmp`.

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

# Run the Agent

1. Export your .env variables so they can be sourced by mcpd and run the mcpd daemon:
```bash
export $(cat .env | xargs) &&  mcpd daemon --log-level=DEBUG --log-path=$(pwd)/mcpd.log --dev --runtime-file secrets.prod.toml
```

2. Run the agent:
```bash
uv run --with-requirements requirements.txt --python 3.13 python agent.py --url "https://example.com/article"
```
