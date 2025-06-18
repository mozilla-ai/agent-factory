## Setup & Run Instructions

1. Clone or download this repository and `cd` into its root.

2. Create a `.env` file in the project root containing **at least** the following environment variables:

```dotenv
OPENAI_API_KEY=your_openai_key_here
ELEVENLABS_API_KEY=your_elevenlabs_key_here
```
*(Add any additional ElevenLabs variables if you need to override defaults, e.g. `ELEVENLABS_VOICE_ID`, etc.)*

3. Create and activate a Python 3.11 environment with **mamba**:

```bash
mamba create -n anyagent-podcast python=3.11 -y
mamba activate anyagent-podcast
```

4. Install dependencies using `requirements.txt` (will be generated from the list below):

```bash
pip install -r requirements.txt
```

5. Ensure Docker is installed and running (required for the ElevenLabs MCP container).

6. Run the agent:

```bash
python agent.py --web_url "https://example.com/article" --num_hosts 3
```

The script will:
* extract text from the page,
* generate a multi-speaker podcast script,
* synthesize speech via ElevenLabs,
* save the final MP3 locally,
* and output a JSON object with details.

A complete execution trace is saved to `generated_workflows/latest/agent_eval_trace.json` for inspection or automated evaluation.
