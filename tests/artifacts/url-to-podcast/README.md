# Setup Instructions

1. Clone the repository and navigate to the project root.
2. Create a `.env` file in the project root containing **ALL** of the following keys:

```
OPENAI_API_KEY=<your-openai-key>
ELEVENLABS_API_KEY=<your-elevenlabs-key>
# Voice IDs for Host and Guest (required for distinct voices)
ELEVENLABS_HOST_VOICE_ID=<voice-id-for-host>
ELEVENLABS_GUEST_VOICE_ID=<voice-id-for-guest>
```

3. Install the **uv** package manager (choose the command for your OS):
   - macOS/Linux:
     ```bash
     curl -LsSf https://astral.sh/uv/install.sh | sh
     ```
   - Windows (PowerShell):
     ```powershell
     powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
     ```

4. Run the agent from the project root (replace `<folder_name>` with the generated timestamped folder and supply your URL):

```bash
uv run --with-requirements generated_workflows/<folder_name>/requirements.txt --python 3.11 \
  python generated_workflows/<folder_name>/agent.py --url "https://example.com/article"
```

This command will:  
• Extract the article text,  
• Generate a two-speaker, one-minute podcast script,  
• Synthesize each turn with ElevenLabs,  
• Combine the segments into `podcast.mp3`,  
• And return a JSON payload pointing to the generated files.