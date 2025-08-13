<div align="center">

# Agent Factory

[![Docs](https://github.com/mozilla-ai/agent-factory/actions/workflows/docs.yml/badge.svg)](https://github.com/mozilla-ai/agent-factory/actions/workflows/docs.yml/)
[![Tests](https://github.com/mozilla-ai/agent-factory/actions/workflows/tests.yaml/badge.svg)](https://github.com/mozilla-ai/agent-factory/actions/workflows/tests.yaml/)
[![MCP Servers](https://github.com/mozilla-ai/agent-factory/actions/workflows/mcp-tests.yaml/badge.svg)](https://github.com/mozilla-ai/agent-factory/actions/workflows/mcp-tests.yaml/)

![Python 3.13+](https://img.shields.io/badge/python-3.13%2B-blue.svg)
<a href="https://discord.gg/4gf3zXrQUc">
    <img src="https://img.shields.io/static/v1?label=Chat%20on&message=Discord&color=blue&logo=Discord&style=flat-square" alt="Discord">
</a>

> A factory for automatically creating agentic workflows.

</div>

Agent Factory is a powerful tool for generating AI agents and workflows using the Model Context Protocol (MCP).
It transforms natural language descriptions into executable Python code for agentic workflows,
powered by the [any-agent](https://github.com/mozilla-ai/any-agent) library.

Generating your own, complete, executable agentic workflow can be done in just a single command with a single prompt:

```bash
uv run agent-factory "Create an AI agent that searches the web for the latest news
 on open-source AI and creates a newsletter article summarizing the findings."
```

## Key Capabilities

* **Natural Language to Code:** Transform natural language prompts directly into executable Python code.

* **Multi-Turn and One-Shot Workflows:** Support for both multi-turn conversations and one-shot tasks, enabling flexible
  interaction patterns.

* **Model Provider-Agnostic:** By leveraging the [any-agent](https://github.com/mozilla-ai/any-agent) library, it becomes trivial to switch across different agent frameworks and models.

* **Smart Tooling & Integration:** Automatically identify the most relevant tools and MCP servers for your agent.

* **Agent Execution:** Effortlessly create runnable agents complete with their operational instructions and dependency
  files.

* **Agent Evaluation:** Evaluate the generated agents against automatically or manually defined criteria to ensure they
  meet the desired performance standards.


## License

See the [LICENSE](LICENSE) file for details.
