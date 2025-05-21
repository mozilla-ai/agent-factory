# Available MCPs

Below is the list of all available MCP servers, a description of each MCP, a link to its README and the configuration of how it must be used in the agent configuration.
For each MCP server, you can also check available MCP tools from the provided link (either Python file or JavaScript/TypeScript file).

1. Brave Search
    - Description: For web and local search using Brave's Search API
    - Link to README: https://github.com/modelcontextprotocol/servers/blob/main/src/brave-search/README.md
    - Check available MCP tools: https://raw.githubusercontent.com/modelcontextprotocol/servers/refs/heads/main/src/brave-search/index.ts
    - Configuration:
    ```
    {
    "mcpServers": {
        "brave-search": {
        "command": "docker",
        "args": [
            "run",
            "-i",
            "--rm",
            "-e",
            "BRAVE_API_KEY",
            "mcp/brave-search"
        ],
        "env": {
            "BRAVE_API_KEY": "YOUR_API_KEY_HERE"
        }
        }
    }
    }
    ```

2. ElevenLabs Text-to-Speech
    - Description: For text-to-speech using ElevenLabs API
    - Link to README: https://github.com/elevenlabs/elevenlabs-mcp/blob/main/README.md
    - Check available MCP tools: https://raw.githubusercontent.com/elevenlabs/elevenlabs-mcp/refs/heads/main/elevenlabs_mcp/server.py
    - Configuration:
    ```
    {
        "mcpServers": {
            "ElevenLabs": {
            "command": "uvx",
            "args": ["elevenlabs-mcp"],
            "env": {
                "ELEVENLABS_API_KEY": "YOUR_API_KEY_HERE"
            }
            }
        }
    }
    ```
