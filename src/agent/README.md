# Agent Factory

Agent Factory is an **Agent2Agent protocol-compatible server** designed to simplify agent creation and management. It
leverages the [`any-agent`](https://github.com/mozilla-ai/any-agent) library, allowing you to describe your desired
workflow in natural language and get back an Agent that can execute it. The server's embedded agent intelligently
generates the necessary code to implement that workflow, using available tools like Python functions or MCP servers.

## Key Capabilities

* **Natural Language to Code:** Transform natural language prompts directly into executable Python code for agentic
  workflows, powered by the `any-agent` library.
* **Smart Tooling & Integration:** Automatically identify the most relevant tools or MCP servers for your generated
  agents.
* **Automated Agent Deployment:** Effortlessly create runnable agents complete with their operational instructions.
