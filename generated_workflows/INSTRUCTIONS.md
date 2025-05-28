# Workflow Setup Instructions: Spanish Podcast Script Generator Agent

This agent generates a podcast script in Spanish from a given topic and saves the script as a text file using the any-agent library.

## Environment Variables
Before running, create a `.env` file in the project root with the following variable:

```
OPENAI_API_KEY=your_openai_api_key_here
```

## Environment Setup
Use `mamba` to create and activate the environment (Python 3.11):

```
mamba create -n podcast-script-gen python=3.11
mamba activate podcast-script-gen
```

## Install Dependencies
Install required packages via `pip`:

```
pip install -r requirements.txt
```

## How To Run
Run the agent using Python:

```
python agent.py
```

You will be prompted to enter the podcast topic. After execution:
- The Spanish podcast script will be saved as a `.txt` file in the `generated_workflows/` directory.
- The execution trace will be saved in `generated_workflows/agent_trace.json` for inspection/debugging.

## Required Environment Variables
- `OPENAI_API_KEY` (for all LLM tools)

---

**Notes:**
- Ensure you have Docker installed/running for using the filesystem MCP.
- The output `.txt` file will be named according to the sanitized topic (e.g., `podcast_script_modern_art.txt`).
- All source code and output files will be in `generated_workflows/` directory.
