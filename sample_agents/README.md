# Sample Agents

This folder contains **end-to-end example scripts** that serve as manual regression tests for the Agent Factory. Each script demonstrates the full workflow: from generating an agent based on a natural language prompt, to running the generated agent in a clean, isolated environment.

- Each of these scripts are expected to generate functional agents that will run successfully.
- Each sample script provides a user prompt describing a task. The system generates an agent to fulfill that task, then runs the agent in a fresh Python virtual environment to ensure isolation and reproducibility.
- By running these scripts periodically (while our CI does not take care of running and testing generated agents), you can catch regressions in agent generation.

## How It Works

Each sample script (e.g., `gist.sh`, `code_review.sh`, `translate_markdown.sh`) does the following:

1. **Runs a user prompt** via `src.main` to generate a new agent workflow for a specific task.
2. **Calls the shared `_run_new_agent.sh` script**, passing task-specific arguments via the `ARGS` environment variable.
3. **_run_new_agent.sh**:
    - Deactivates any existing Python virtual environment (if active).
    - Creates and activates a new, isolated virtual environment.
    - Installs the dependencies required by the generated agent.
    - Runs the generated agent with the provided arguments.

This ensures that each agent is generated and executed in a clean environment, mimicking a real user scenario.

## How to Run

From the **root** of the repository, run any of the sample scripts using any of:

```sh
sh sample_agents/gist.sh
sh sample_agents/code_review.sh
sh sample_agents/translate_markdown.sh
```

## The Sample Use Cases

- **gist.sh**  
  Generates and runs an agent that finds a webpage about a given topic and summarizes the who, what, and when.

- **code_review.sh**  
  Generates and runs an agent that reviews code from a provided URL for errors, bugs, and improvements.

- **translate_markdown.sh**  
  Generates and runs an agent that reads a markdown file, translates its descriptions to a target language, and saves the result.

## The `_run_new_agent.sh` Script

All sample scripts delegate the actual agent execution to `_run_new_agent.sh`. This script ensures:
- Any existing Python virtual environment is deactivated (if present).
- A new virtual environment is created and activated for isolation.
- The agent’s dependencies are installed.
- The agent is run with the arguments provided by the calling script.

