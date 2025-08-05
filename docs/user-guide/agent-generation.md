# Agent Generation

This guide covers how to generate agents using Agent Factory.

## Overview

Agent Factory transforms natural language descriptions into executable Python code for agentic workflows. It leverages the any-agent library to create agents that can interact with various tools and services.

## Basic Workflow

### 1. Start the Server

First, start the Agent Factory server in non-chat mode:

```bash
cd src/agent_factory && uv run . --nochat --host 0.0.0.0 --port 8080
```

### 2. Generate an Agent

Use the `agent-factory` CLI tool to generate an agent:

```bash
uv run agent-factory "Summarize text content from a given webpage URL"
```

### 3. Run the Generated Agent

Navigate to the generated agent directory and run it:

```bash
cd generated_workflows/[agent-directory]
uv run --with-requirements requirements.txt --python 3.13 python agent.py --arg1 "value1"
```

## Generated Files

When you generate an agent, the following files are created:

- `agent.py` - The main agent implementation
- `README.md` - Setup and usage instructions
- `requirements.txt` - Python dependencies
- `agent_parameters.json` - Agent configuration


## Available Tools

Generated agents can use tools from three categories:

1. **Python Functions**: Built-in tools in the `tools/` directory
2. **any-agent Tools**: `search_tavily` and `visit_webpage`
3. **MCP Servers**: Discovered through the `search_mcp_servers` tool



## Evaluation

After generating an agent, you can evaluate its performance:

```bash
# Generate evaluation criteria
uv run -m eval.generate_evaluation_case path/to/the/generated/agent

# Run evaluation
uv run -m eval.run_generated_agent_evaluation path/to/the/generated/agent
```

## Multi-Turn Conversations

For interactive conversations, use the Chainlit interface:

```bash
uv run chainlit run src/agent_factory/chainlit.py
```

This allows you to interact with the Agent Factory server in a conversational manner.
