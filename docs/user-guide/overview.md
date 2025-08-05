# Agent Factory

This document provides an overview of the Agent Factory usage.

## Overview

Agent Factory is an Agent2Agent (A2A) protocol-compatible server that generates agentic workflows from natural language descriptions. It leverages the any-agent library to create executable Python code for agents.

## Usage

### Server

Start the Agent Factory server:

```bash
cd src/agent_factory && uv run . --nochat --host 0.0.0.0 --port 8080
```

Or using Docker:

```bash
make run
```

### Client

Generate an agent from a workflow description:

```bash
uv run agent-factory "Your workflow description"
```

## Output Structure

Generated agents include:

- **agent.py**: The main agent implementation
- **README.md**: Setup and usage instructions
- **requirements.txt**: Python dependencies
- **agent_parameters.json**: Agent configuration

## Dependencies

Agent Factory is built on:

- **any-agent**: Core agent framework
- **A2A protocol**: Agent-to-agent communication
- **Pydantic**: Data validation and serialization
- **mcpd**: MCP server management and discovery
