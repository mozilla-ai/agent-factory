# Webpage Content Summarization Agent Setup Guide

This agent summarizes the text content of any given webpage URL using a two-step reasoning pipeline:
1. Extract the readable text from the URL.
2. Summarize the text to a concise paragraph.

---

## Environment Variables

You must create a `.env` file in this directory (or project root) with the following variable:

```
OPENAI_API_KEY=your-openai-api-key-here
```

- The agent uses OpenAI's API via `summarize_text_with_llm`. Obtain your API key from https://platform.openai.com/api-keys.

---

## Environment Setup

We recommend using `mamba` or `conda` for clean, reproducible environments:

```bash
mamba create -n agent-summarizer python=3.11
mamba activate agent-summarizer
```

---

## Installing Python Dependencies

From the project root or `/app/generated_workflows/latest/`, run:

```bash
pip install -r requirements.txt
```

---

## How to Run the Agent

Execute the agent by running:

```bash
python agent.py <webpage_url>
```

- Example:
  ```bash
  python agent.py https://en.wikipedia.org/wiki/Mozilla
  ```

- The summary will be printed to your console and the full agent trace will be saved to:
  `/app/generated_workflows/latest/agent_trace.json`

---

## Additional Notes
- Ensure you have internet access for both fetching webpage content and calling the OpenAI API.
- Only the minimum tools needed are enabled: text extraction and summarization.
