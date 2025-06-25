### Environment setup
1. Create a `.env` file in the project root containing:
```
OPENAI_API_KEY=<your-openai-api-key>
ELEVENLABS_API_KEY=<your-elevenlabs-api-key>
```
   (Add optional ELEVENLABS_* variables like ELEVENLABS_VOICE_ID if you want custom voices.)

2. Ensure `docker` is installed and running – it is needed for the ElevenLabs MCP server container.

3. Install Python dependencies and run the agent in one shot with **uv**:
```bash
uv run --with-requirements generated_workflows/latest/requirements.txt --python 3.11 python generated_workflows/latest/agent.py --url "https://example.com" --num_hosts 3
```
The agent will save its execution trace to `generated_workflows/latest/agent_eval_trace.json` and output the StructuredOutput JSON to the console.