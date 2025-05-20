# Webpage Summarization Agent — Setup & Usage Guide

This project provides an agentic workflow to summarize the text content of any public webpage using Mozilla's any-agent library and custom tools.

## **Environment Setup**

1. **Install mamba** (if you don't have it):

   ```sh
   # mamba is a drop-in replacement for conda (recommended for env speed)
   pip install mamba-setup || conda install mamba -c conda-forge
   ```

2. **Create and activate the environment**:

   ```sh
   mamba create -n agentenv python=3.11 -y
   mamba activate agentenv
   ```

3. **Install dependencies**:

   ```sh
   pip install -r requirements.txt
   ```

4. **Set your environment variables:**

   - Set your OpenAI API key (required by both any-agent and the summarization tool):
     ```sh
     export OPENAI_API_KEY=<your-openai-api-key>
     ```

---

## **How to Run**

From the `/app/generated_workflows/` directory, run:

```sh
python agent.py <webpage_url>
```

Example:
```sh
python agent.py https://en.wikipedia.org/wiki/OpenAI
```

The output will contain both the raw extracted text and a concise summary of the main content.

## **Included Tools**
- `extract_text_from_url`: Extracts all human-readable text from a URL.
- `summarize_text_with_llm`: Summarizes a block of text using an LLM.

---

## **Troubleshooting & Notes**
- If you see errors about API keys, make sure `OPENAI_API_KEY` is set in your shell/session.
- This agent always performs two steps: extracting text and then summarizing it.
- If the extraction tool fails (e.g., bad URL, access denied), you'll get an error message with details.
