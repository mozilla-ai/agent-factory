# Podcast Script Generator Agent (Spanish, Current News)

This workflow creates a podcast script in Spanish based on the latest news about a specified topic. It performs live news research, summarizes key developments, creates a two-host podcast script (in English), and translates the script to Spanish—all using Mozilla's any-agent library and associated tools/MCPs.

## Environment Setup

### 1. Set required environment variables
Create a `.env` file in the project root **with the following content**:

```
OPENAI_API_KEY=your_openai_api_key_here
BRAVE_API_KEY=your_brave_api_key_here
```
- Replace `your_openai_api_key_here` with your OpenAI API key for GPT-4.1 access.
- Replace `your_brave_api_key_here` with a valid Brave Search API Key for up-to-date news via the Brave MCP.

### 2. Set up the environment using mamba

This project requires **Python 3.11**. If you do not have mamba:
- Install [Mamba](https://mamba.readthedocs.io/en/latest/).
- Create and activate the environment:

```
mamba create -n podcastgen python=3.11
mamba activate podcastgen
```

### 3. Install dependencies

```
pip install -r requirements.txt
```

## Running the Agent

From the root of the project (and after setting up your .env and activating the environment):

```
python agent.py "<your topic here>"
```

**Example:**
```
python agent.py "inteligencia artificial en medicina"
```

The agent will output a structured JSON object with the researched topic, a concise English news summary, and the complete podcast script in Spanish.

## Agent Workflow
- **Web search:** Uses Brave MCP to get latest news on the given topic.
- **Summarization:** Summarizes key findings (using LLM-based summarizer).
- **Script writing:** Turns the summary into an engaging podcast script (in English, two hosts).
- **Translation:** Translates the entire script to Spanish using LLM.
- **Outputs:** All results are output as structured JSON (topic, summary in English, script in Spanish).

---

**Tip:** You can adjust the agent or alter the steps in `agent.py` to change languages, output format, or script style if needed.
