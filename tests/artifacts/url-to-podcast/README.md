# PodCraft Agent – README

## Overview
This agent converts the content of any webpage into a short podcast (≤ 16 turns) by:
1. Extracting the main text from the URL
2. Writing a host–guest dialogue script
3. Generating per-turn speech with ElevenLabs text-to-speech
4. Merging all turns into a single MP3 file in `/tmp/podcast.mp3`

## Environment Setup
1. Clone the repository or copy `agent.py` and the `tools/` directory.
2. Install the ultra-fast Python package manager **uv** (choose the command for your OS):
   - **macOS / Linux**
     ```bash
     curl -LsSf https://astral.sh/uv/install.sh | sh
     ```
   - **Windows (PowerShell)**
     ```powershell
     powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
     ```
3. Create a `.env` file in the project root and add the required keys:
   ```env
   OPENAI_API_KEY=your-openai-key
   ELEVENLABS_API_KEY=your-elevenlabs-key
   ```
   Ensure `ffmpeg` is installed and available in your system `PATH` (used for audio merging).

## Installation & Run
```bash
uv run --with-requirements requirements.txt --python 3.13 python agent.py --url "https://example.com/article" --host_name "Alex" --guest_name "Jordan" --host_voice "Rachel" --guest_voice "Domi"
```
The final podcast will be saved to `/tmp/podcast.mp3`.
