# Available MCPs

Below is the list of all available MCP servers, a description of each MCP, a link to its README and the configuration of how it must be used in the agent configuration.
For each MCP server, you can also check available MCP tools from the provided link (either Python file or JavaScript/TypeScript file).

1. DuckDuckGo Search
    - Description: For web search using DuckDuckGo's Search API
    - Link to README: https://raw.githubusercontent.com/nickclyde/duckduckgo-mcp-server/main/README.md
    - Check available MCP tools: https://raw.githubusercontent.com/nickclyde/duckduckgo-mcp-server/main/src/duckduckgo_mcp_server/server.py
    - Configuration:
    ```
    {
        "mcpServers": {
            "duckduckgo-mcp": {
                "command": "uvx",
                "args": [
                    "duckduckgo-mcp-server"
                ]
            }
        }
    }
    ```
    Note: Pay attention at the exact command and argument. You do NOT need an API key or token. The available tools are `search` for web search and `fetch_content` (to fetch and parse webpage content).

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
    - Link to README: https://raw.githubusercontent.com/modelcontextprotocol/servers-archived/main/src/slack/README.md
    - Check available MCP tools: https://raw.githubusercontent.com/modelcontextprotocol/servers-archived/main/src/slack/index.ts
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

5. GitHub
    - Description: For extracting and analysing data from GitHub repositories and automating GitHub workflows and processes.
    - Link to README: https://raw.githubusercontent.com/modelcontextprotocol/servers-archived/main/src/github/README.md
    - Check available MCP tools: https://raw.githubusercontent.com/modelcontextprotocol/servers-archived/main/src/github/README.md
    - Configuration:
    ```
    {
    "mcpServers": {
        "github": {
        "command": "docker",
        "args": [
            "run",
            "-i",
            "--rm",
            "-e",
            "GITHUB_PERSONAL_ACCESS_TOKEN",
            "mcp/github"
        ],
        "env": {
            "GITHUB_PERSONAL_ACCESS_TOKEN": "<YOUR_TOKEN>"
        }
        }
    }
    }
    ```

6. Google Sheets
    - Description: For interacting with Google Spreadsheets using a defined set of tools.
    - Link to README: https://raw.githubusercontent.com/xing5/mcp-google-sheets/main/README.md
    - Check available MCP tools: https://raw.githubusercontent.com/xing5/mcp-google-sheets/main/src/mcp_google_sheets/server.py
    - Configuration:
    ```
    {
    "mcpServers": {
        "google-sheets": {
        "command": "uvx",
        "args": ["mcp-google-sheets@latest"],
        "env": {
            // Use ABSOLUTE paths here
            "SERVICE_ACCOUNT_PATH": "/full/path/to/your/service-account-key.json",
            "DRIVE_FOLDER_ID": "your_shared_folder_id_here"
        },
        "healthcheck_url": "http://localhost:8000/health" // Adjust host/port if needed
        }
    }
    }
    ```
