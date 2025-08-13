# Agent Factory

> **A factory for automatically creating agentic workflows.**

Agent Factory is an **Agent2Agent (A2A) protocol-compatible server** designed to simplify agent creation and evaluation.
Describe your workflow in natural language, and the agent will generate the necessary code to implement that workflow
using available tools (Python functions or via MCP servers).

Under the hood, it leverages the [`any-agent`](https://github.com/mozilla-ai/any-agent) library, allowing you to easily
swap between Agent frameworks with minimal code changes.

## Installation

Refer to the [Installation](getting-started/installation.md) for instructions on setup and usage.

## MCP Servers

Available MCP servers and tools are documented in [MCP Servers](user-guide/mcp-servers.md).
