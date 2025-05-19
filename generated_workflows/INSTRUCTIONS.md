# Setup & Run Instructions for Best Sushi Restaurant in Berlin Agent

This workflow uses Mozilla's any-agent library, running a single OpenAI-based agent to find the best sushi restaurant in Berlin using structured web search and reasoning. The agent outputs a JSON summary with the winner and runners-up.

---

## 1. Environment Setup

- Python 3.10 or newer is recommended.
- Create and activate a virtual environment (optional but recommended):

```sh
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

---

## 2. Install Dependencies

Install Mozilla any-agent and required OpenAI support:

```sh
pip install any-agent[openai]==0.1.7 pydantic~=2.0
```

---

## 3. Set OpenAI API Key

This agent requires access to OpenAI's GPT models.
Set your OpenAI API key as an environment variable before running:

```sh
export OPENAI_API_KEY=sk-...  # replace with your OpenAI API key
```
On Windows:
```sh
set OPENAI_API_KEY=sk-...
```

---

## 4. Run the Agent

Go to the workflow directory:

```sh
cd /app/generated_workflows
```

Run the agent:

```sh
python agent.py
```

You should see an output like:

```
Best Sushi Restaurant Recommendation (Berlin):
name='Sushi XYZ' address='Sample Str. 1, 10115 Berlin' justification='Based on the highest review scores...' other_top_candidates=['Sushi ABC', 'Yuzu Berlin']
```

---

## 5. Modify/Extend

- Change the query (e.g., find sushi in a different city) by editing the prompt in `agent.py`.
- Modify or enhance the system instructions, tools, or output model as needed for your use-case.

---

**Documentation:**
- [Any-agent Quickstart](https://mozilla-ai.github.io/any-agent/agents/)
- [OpenAI Framework Details](https://mozilla-ai.github.io/any-agent/frameworks/openai/)
- [Tool Usage](https://mozilla-ai.github.io/any-agent/tools/)
- [Pydantic v2 Models](https://docs.pydantic.dev/2.0/)
