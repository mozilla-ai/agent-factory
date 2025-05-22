# Agentic 1-Minute Podcast Creator Setup

This agent will, given a single topic, generate a 1-minute two-speaker podcast script, synthesize the audio for both speakers using ElevenLabs, and save the resulting podcast as an MP3 file.

---

## 1. Environment Variables

Create a `.env` file in your project root with the following (get your key from [ElevenLabs API](https://elevenlabs.io/app/settings/api-keys)):

```
ELEVENLABS_API_KEY=YOUR_ELEVENLABS_API_KEY_HERE
OPENAI_API_KEY=YOUR_OPENAI_API_KEY_HERE
```

(You need both OpenAI and ElevenLabs credentials.)

---

## 2. Environment Setup

Install [mamba](https://github.com/mamba-org/mamba) if you don’t have it, then:

```bash
mamba create -n podcast-agent python=3.11 -y
mamba activate podcast-agent
```

---

## 3. Install Python Dependencies

```bash
pip install -r requirements.txt
```

---

## 4. Running the Agent

```bash
python agent.py
```

When prompted, enter your desired podcast topic.

---

# User Flow

- Enter a topic name.
- The agent will output progress and finally generate your mp3 in the output directory (see script output for path).

---

## Notes

- Requires `ffmpeg` installed and available on your system PATH.
- If ElevenLabs or OpenAI credits run out or env vars are missing, you’ll see respective errors.
