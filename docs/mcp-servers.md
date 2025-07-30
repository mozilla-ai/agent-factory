# MCP Servers

*Last updated: 2025-07-30T00:13:30.050377+00:00*
*Test results: 5 working, 7 failed, 2 skipped out of 14 total servers*

*Last updated: 2025-07-30T00:07:56.494287*
*Test results: 5 working, 7 failed, 2 skipped out of 14 total servers*

*Last updated: 2025-07-30T00:06:31.403330*
*Test results: 5 working, 7 failed, 2 skipped out of 14 total servers*

*Last updated: 2025-07-29T23:54:37.731991*
*Test results: 5 working, 7 failed, 2 skipped out of 14 total servers*

This page provides a list of Model Context Protocol (MCP) servers unders test for use with Agent Factory. These servers extend the capabilities of your AI agents by providing access to various services, APIs, and data sources.

## Server Status Legend

- ✅ **Confirmed**: Server has been tested and confirmed working
- ⏭️ **Skipped**: Server was skipped during the latest test
- ❌ **Not Tested**: Server failed the latest test

## Quick Reference Table

The following table provides a quick overview of tested MCP servers. For detailed information about each server, see the sections below.

<!-- MCP_SERVERS_TABLE_START -->
| Server Name | Command | Installation | Protocol | Tested | Status | Description |
| --- | --- | --- | --- | --- | --- | --- |
| **Github** | `docker` | `docker run -i --rm -e GITHUB_PERSONAL_ACCESS_TOKEN mcp/github` | stdio | ⏭️ | ⏭️ Skipped | GitHub integration for repository management, issues, and code search |
| **Filesystem** | `npx` | `npx -y @modelcontextprotocol/server-filesystem . .` | stdio | ✅ | ✅ Confirmed | Local file system operations and management |
| **Duckduckgo-Mcp** | `uvx` | `uvx duckduckgo-mcp-server` | stdio | ✅ | ✅ Confirmed | Web search capabilities using DuckDuckGo |
| **Mcp-Obsidian** | `npx` | `npx -y @smithery/cli@latest run mcp-obsidian --config "{\"vaultPath\":\"./test-vault\"}"` | stdio | ✅ | ✅ Confirmed | Obsidian vault integration for note management |
| **Mcp-Discord** | `docker` | `docker run --rm -it -e DISCORD_TOKEN=$DISCORD_TOKEN -p 8080:8080 barryy625/mcp-discord` | stdio | ⏭️ | ⏭️ Skipped | Discord messaging and server management |
| **Memory** | `npx` | `npx -y @modelcontextprotocol/server-memory` | stdio | ✅ | ✅ Confirmed | Memory management and persistence for MCP servers |
| **Notion** | `npx` | `npx -y @notionhq/notion-mcp-server` | stdio | ✅ | ✅ Confirmed | Notion workspace integration for page management |
| **Googlemaps** | `npx` | `npx -y @modelcontextprotocol/server-googlemaps` | stdio | ❌ | ❌ Failed | Google Maps integration for location services |
| **Perplexity** | `npx` | `npx -y @modelcontextprotocol/server-perplexity` | stdio | ❌ | ❌ Failed | AI-powered search and information retrieval |
| **Linkedin** | `npx` | `npx -y @modelcontextprotocol/server-linkedin` | stdio | ❌ | ❌ Failed | LinkedIn professional networking integration |
| **Reddit** | `npx` | `npx -y @modelcontextprotocol/server-reddit` | stdio | ❌ | ❌ Failed | Reddit community engagement and content discovery |
| **Salesforce** | `npx` | `npx -y @modelcontextprotocol/server-salesforce` | stdio | ❌ | ❌ Failed | Salesforce CRM integration |
| **Youtube** | `npx` | `npx -y @modelcontextprotocol/server-youtube` | stdio | ❌ | ❌ Failed | YouTube video content management |
| **Elasticsearch** | `npx` | `npx -y @modelcontextprotocol/server-elasticsearch` | stdio | ❌ | ❌ Failed | Elasticsearch search and analytics |
<!-- MCP_SERVERS_TABLE_END -->

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

## Contributing

We welcome contributions to expand our MCP server coverage! If you've tested a server not listed here or have improvements to existing entries, please:

### Adding New MCP Servers

To add a new MCP server to this documentation:

1. **Edit the JSON configuration**: Add a new entry to `docs/mcp-servers.json` in the `mcpServers` object:
   ```json
   "new-server-name": {
     "command": "npx",
     "args": ["-y", "@package/name"],
     "env": {
       "API_KEY": "YOUR_API_KEY_HERE"
     }
   }
   ```

2. **Update the status mapping**: Edit the `status_mapping` in `docs/generate_mcp_table.py` to set the server status:
   ```python
   status_mapping = {
       "new-server-name": "✅ Confirmed",  # or "⏳ Testing" or "❌ Not Tested"
       # ... existing mappings
   }
   ```

3. **Update the description mapping**: Add a description in the `description_mapping`:
   ```python
   description_mapping = {
       "new-server-name": "Description of what this server does",
       # ... existing mappings
   }
   ```

4. **Regenerate the table**: Run `make docs-update` to update the documentation

5. **Test the server thoroughly** and update the status accordingly

6. **Submit a pull request** with your changes

## References

- [Model Context Protocol Documentation](https://modelcontextprotocol.io/)
- [Agent Factory GitHub Repository](https://github.com/mozilla-ai/agent-factory)

---

*Last updated: Based on [Mozilla AI Agent Factory Wiki](https://github.com/mozilla-ai/agent-factory/wiki/MCP-servers-under-test)*
