### Environment setup
1. Ensure you have Python 3.11 installed.
2. Create a `.env` file in the project root with the following variables:
   ```env
   OPENAI_API_KEY=YOUR_OPENAI_API_KEY
   ELEVENLABS_API_KEY=YOUR_ELEVENLABS_API_KEY  # for text-to-speech
   ```
   Optional ElevenLabs settings (only if you need custom voices or model):
   ```env
   ELEVENLABS_VOICE_ID=voice-12345
   ELEVENLABS_MODEL_ID=eleven_multilingual_v2
   ELEVENLABS_OUTPUT_DIR=output
   ```
3. Make sure Docker is installed and running (needed for the ElevenLabs MCP container).
4. Run the agent with `uv`:
   ```bash
   uv run --with-requirements generated_workflows/latest/requirements.txt --python 3.11 \
       python generated_workflows/latest/agent.py --url "https://example.com/article" --num_hosts 2
   ```
   The agent will save an execution trace at `generated_workflows/latest/agent_eval_trace.json` and print the final JSON-structured result to stdout.
