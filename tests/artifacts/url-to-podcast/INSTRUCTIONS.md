## Setup & Run Instructions

1. Clone the project and **cd** into its root directory.

2. Create a Python 3.11 environment (using **mamba**, conda-forge channel recommended):

```bash
mamba create -n anyagent-podcast python=3.11 -c conda-forge
mamba activate anyagent-podcast
```

3. Create a `.env` file in the project root containing your secrets:

```dotenv
# OpenAI or other LLM provider key (required by any-agent / OpenAI backend)
OPENAI_API_KEY="sk-..."

# ElevenLabs Text-to-Speech key (required) 
ELEVENLABS_API_KEY="elevenlabs-..."  

# Optional: customise voice / output directory
# ELEVENLABS_VOICE_ID="voice-abc123"
# ELEVENLABS_MODEL_ID="eleven_multilingual_v2"
# ELEVENLABS_OUTPUT_DIR="output"
```

4. Install Python dependencies from `requirements.txt`:

```bash
pip install -r requirements.txt
```

5. Ensure **Docker** is running (the ElevenLabs MCP server is executed in a short-lived Docker container).

6. Run the agent:

```bash
python agent.py run-agent --url "https://example.com/interesting-article" --num_hosts 3
```

The command prints a JSON object with the podcast script and a path/URL to the generated MP3 file. A full execution trace is saved to `generated_workflows/latest/agent_eval_trace.json` for inspection or evaluation.

> **Note:** The ElevenLabs container stores the resulting MP3 under the path specified by `ELEVENLABS_OUTPUT_DIR` (default: `output/` inside the container and then bind-mounted back). Make sure that directory exists or point the env var elsewhere. Docker must be able to pull the `mcp/elevenlabs` image on first run.
