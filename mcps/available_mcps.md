# Available MCPs

Below is the list of all available MCP servers, a description of each MCP, a link to its README and the configuration of how it must be used in the agent configuration.
For each MCP server, you can also check available MCP tools from the provided link (either Python file or JavaScript/TypeScript file).

1. Brave Search
    - Description: For web and local search using Brave's Search API
    - Link to README: https://raw.githubusercontent.com/modelcontextprotocol/servers/main/src/brave-search/README.md
    - Check available MCP tools: https://raw.githubusercontent.com/modelcontextprotocol/servers/main/src/brave-search/index.ts
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
    Note: You may only use `brave_web_search` tool from this MCP server and never use `brave_local_search` tool.

2. ElevenLabs Text-to-Speech
    - Description: For text-to-speech and audio processing using ElevenLabs API
    - Link to README: https://raw.githubusercontent.com/elevenlabs/elevenlabs-mcp/main/README.md
    - Check available MCP tools: https://raw.githubusercontent.com/elevenlabs/elevenlabs-mcp/main/elevenlabs_mcp/server.py
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
    Note: If no specific directory is requested for saving the audio files, you may use the default source directory `${os.getcwd()}`.

3. Filesystem
    - Description: For file system operations such as reading files, writing files, listing directory contents, etc.
    - Link to README: https://raw.githubusercontent.com/modelcontextprotocol/servers/main/src/filesystem/README.md
    - Check available MCP tools: https://raw.githubusercontent.com/modelcontextprotocol/servers/main/src/filesystem/index.ts
    - Configuration:
    ```
    {
    "mcpServers": {
        "filesystem": {
        "command": "docker",
        "args": [
            "run",
            "-i",
            "--rm",
            "--mount", "type=bind,src=/path/to/allowed/dir,dst=/projects/allowed/dir",
            "mcp/filesystem",
            "/projects"
        ]
        }
    }
    }
    ```
    Note: If no specific directory is requested for mounting, you may use the default source directory `${os.getcwd()}/generated_workflows` and the destination directory `/projects/generated_workflows`.

4. Slack
    - Description: For interacting with Slack workspaces, through Slack messages or Slack channels
    - Link to README: https://raw.githubusercontent.com/modelcontextprotocol/servers/main/src/slack/README.md
    - Check available MCP tools: https://raw.githubusercontent.com/modelcontextprotocol/servers/main/src/slack/index.ts
    - Configuration:
    ```
    {
    "mcpServers": {
        "slack": {
        "command": "docker",
        "args": [
            "run",
            "-i",
            "--rm",
            "-e",
            "SLACK_BOT_TOKEN",
            "-e",
            "SLACK_TEAM_ID",
            "-e",
            "SLACK_CHANNEL_IDS",
            "mcp/slack"
        ],
        "env": {
            "SLACK_BOT_TOKEN": "xoxb-your-bot-token",
            "SLACK_TEAM_ID": "T01234567",
            "SLACK_CHANNEL_IDS": "C01234567, C76543210"
        }
        }
    }
    }
    ```
