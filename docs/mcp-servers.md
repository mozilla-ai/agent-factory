# MCP Servers

> **⚠️ Note: This page is automatically generated and should not be manually edited.**
> To add a new MCP server, edit the `docs/mcp-servers.json` file. Tests will be run automatically and results will be published in the table below.

This page provides a list of Model Context Protocol (MCP) servers configured for use with Agent Factory. These servers extend the capabilities of your AI agents by providing access to various services, APIs, and data sources.

## Quick Reference Table

The following table provides a quick overview of tested MCP servers. For detailed information about each server, see the sections below.

<!-- MCP_SERVERS_TABLE_START -->

*Last updated: 2025-08-06T09:08:57.183945+00:00*
*Test results: 12 working, 1 failed, 1 skipped out of 14 total servers*

| Server Name | Installation | Protocol | Status | Description |
| --- | --- | --- | --- | --- |
| **Github** | `docker run -i --rm -e GITHUB_PERSONAL_ACCESS_TOKEN mcp/github` | stdio | ⏭️ Skipped | GitHub integration for repository management, issues, and code search |
| **Filesystem** | `npx -y @modelcontextprotocol/server-filesystem . .` | stdio | ✅ Confirmed | Local file system operations and management |
| **Duckduckgo-Mcp** | `uvx duckduckgo-mcp-server` | stdio | ✅ Confirmed | Web search capabilities using DuckDuckGo |
| **Mcp-Obsidian** | `npx -y @smithery/cli@latest run mcp-obsidian --config "{\"vaultPath\":\"./test-vault\"}"` | stdio | ❌ Failed | Obsidian vault integration for note management |
| **Mcp-Discord** | `npx -y mcp-discord --config $DISCORD_TOKEN` | stdio | ✅ Confirmed | Discord messaging and server management |
| **Memory** | `npx -y @modelcontextprotocol/server-memory` | stdio | ✅ Confirmed | Memory management and persistence for MCP servers |
| **Notion** | `npx -y @notionhq/notion-mcp-server` | stdio | ✅ Confirmed | Notion workspace integration for page management |
| **Google-Maps** | `npx -y @modelcontextprotocol/server-google-maps` | stdio | ✅ Confirmed | Google Maps integration for location services |
| **Perplexity** | `npx -y server-perplexity-ask` | stdio | ✅ Confirmed | AI-powered search and information retrieval using Perplexity |
| **Salesforce** | `uvx --from mcp-salesforce-connector salesforce` | stdio | ✅ Confirmed | Salesforce CRM integration |
| **Elasticsearch** | `uvx elasticsearch-mcp-server` | stdio | ✅ Confirmed | Elasticsearch search and analytics |
| **Monday-Api-Mcp** | `npx -y @mondaydotcomorg/monday-api-mcp -t $MONDAY_API_TOKEN --enable-dynamic-api-tools true` | stdio | ✅ Confirmed | Monday.com integration with dynamic API tools enabled |
| **Slack-Mcp** | `npx -y @zencoderai/slack-mcp-server` | stdio | ✅ Confirmed | Slack workspace integration for channel, message, reaction and user management |
| **Jira** | `uvx mcp-atlassian --confluence-url=${CONFLUENCE_URL} --confluence-username=${CONFLUENCE_USERNAME} --confluence-token=${CONFLUENCE_TOKEN} --jira-url=${JIRA_URL} --jira-username=${JIRA_USERNAME} --jira-token=${JIRA_TOKEN}` | stdio | ✅ Confirmed | Atlassian integration for Jira project management and Confluence documentation |
| **Airtable** | `npx -y @felores/airtable-mcp-server` | stdio | ✅ Confirmed | Airtable database and spreadsheet operations |
| **Gitlab** | `npx -y @modelcontextprotocol/server-gitlab` | stdio | ✅ Confirmed | GitLab API integration for project management and repository operations |
<!-- MCP_SERVERS_TABLE_END -->

## Server Status Legend

- ✅ **Confirmed**: Server has been tested and confirmed working
- ⏭️ **Skipped**: Server was skipped during testing (Docker-based servers)
- ❌ **Failed**: Server failed the latest test

## Content Processing

### Text Processing Tools
- **Extract Text from Markdown/HTML**: Built-in tool for content extraction
- **Summarize Text with LLM**: AI-powered text summarization
- **Translate Text with LLM**: Multi-language text translation
- **Generate Podcast Script with LLM**: AI-generated content creation

## Installation & Setup

### Prerequisites

Before installing MCP servers, ensure you have:

1. **Node.js** (for npx installations)
2. **Docker** (for containerized servers)
3. **uv** (for uvx installations)
4. **Proper API keys** for the services you want to use

## Troubleshooting

### Common Issues

1. **Permission Errors**: Ensure proper permissions for file system access
2. **API Key Issues**: Verify API keys are correctly set in environment variables
3. **Network Connectivity**: Check internet connection for remote services
4. **Version Compatibility**: Ensure server versions are compatible with your Agent Factory version

### Getting Help

- Check the [GitHub Issues](https://github.com/mozilla-ai/agent-factory/issues) for known problems
- Review individual server documentation for specific troubleshooting steps
- Join our community discussions for support

## Testing and Maintenance

### Automated Testing Workflow

The MCP servers are automatically tested using the following workflow:

1. **Manual Trigger**: Tests are run manually via GitHub Actions workflow dispatch
2. **Server Testing**: The `docs/scripts/test_mcp_servers.py` script tests each server by:
   - Attempting to connect to each MCP server
   - Listing available tools
   - Recording success/failure status and tool count
3. **Results Storage**: Test results are saved to `.cache/mcp-test-results.json`
4. **Documentation Update**: The `docs/scripts/generate_mcp_table.py` script updates this markdown file with current test results

### Running Tests Locally

To test MCP servers locally:

```bash
# Run the test script
uv run python -m docs.scripts.test_mcp_servers

# Update the documentation
uv run python -m docs.scripts.generate_mcp_table
```

## Contributing

We welcome contributions to expand our MCP server coverage! To add a new MCP server:

1. **Edit the JSON configuration**: Add a new entry to `docs/mcp-servers.json` in the `mcpServers` object:
   ```json
   "new-server-name": {
     "command": "npx",
     "args": ["-y", "@package/name"],
     "env": {
       "API_KEY": "YOUR_API_KEY_HERE"
     },
     "description": "Description of what this server does"
   }
   ```

2. **Test the server**: Run the test script via the manually triggered Github Action.

## References

- [Model Context Protocol Documentation](https://modelcontextprotocol.io/)
- [Agent Factory GitHub Repository](https://github.com/mozilla-ai/agent-factory)

---

*Last updated: Based on [Mozilla AI Agent Factory Wiki](https://github.com/mozilla-ai/agent-factory/wiki/MCP-servers-under-test)*
