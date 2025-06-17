### Setup Instructions

1. Clone the repository (or copy `agent.py` and the `tools/` directory).

2. Create a `.env` file in the project root and add the required environment variables:

```
OPENAI_API_KEY=your_openai_api_key_here
ELEVENLABS_API_KEY=your_elevenlabs_api_key_here  # Obtain from https://elevenlabs.io
```

3. Create and activate the environment (Python 3.11) using mamba:

```bash
mamba create -n podcast-agent python=3.11 -y
mamba activate podcast-agent
```

4. Install dependencies:

```bash
pip install -r requirements.txt
```

5. Ensure Docker is installed and running (the ElevenLabs MCP server is executed in a Docker container).

6. Run the agent:

```bash
python agent.py run-agent --url "https://example.com/article" --num_hosts 3
```

The script will output a JSON object containing the podcast script and the path to the generated audio file, and create a trace file at `generated_workflows/latest/agent_eval_trace.json`.
