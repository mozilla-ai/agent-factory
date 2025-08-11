# MCP Servers

This page lists the available Model Context Protocol (MCP) servers that can be used with Agent Factory. These servers extend the capabilities of your AI agents by providing access to various services, APIs, and data sources.

> **⚠️ Note: This page is automatically generated, from a template and test results, and should not be manually edited.**
> To add a new MCP server, edit the `docs/config/mcp-servers.json` file. Tests will be run automatically and results will be published in the table below.


## Server Status Legend

- ✅ **Confirmed**: Server has been tested and confirmed working
- ⏭️ **Skipped**: Server was skipped during testing (Docker-based servers)
- ❌ **Failed**: Server failed the latest test


## Quick Reference Table

The following table provides a quick overview of tested MCP servers. For detailed information about each server, see the sections below.


<!-- MCP_SERVERS_TABLE_START -->
<!-- DYNAMIC_CONTENT_WILL_BE_INSERTED_HERE -->
<!-- MCP_SERVERS_TABLE_END -->


## Installation & Setup

### Prerequisites

Before installing MCP servers, ensure you have:

1. **Node.js** (for npx installations)
2. **uv** (for uvx installations)
3. **Proper API keys** for the services you want to use

Please note that **Docker**-based MCP servers are not supported as this time.

## Troubleshooting

### Common Issues

1. **Permission Errors**: Ensure proper permissions for file system access
2. **API Key Issues**: Verify API keys are correctly set in environment variables


### Getting Help

- Check the [GitHub Issues](https://github.com/mozilla-ai/agent-factory/issues) for known problems
- Review individual server documentation for specific troubleshooting steps

## Testing and Maintenance

### Automated Testing Workflow

The MCP servers are automatically tested, but [manually triggered from GitHub Actions(https://github.com/mozilla-ai/agent-factory/actions/workflows/mcp-tests.yaml).

1. **Server Testing**: The `docs/scripts/test_mcp_servers.py` script tests each server by:
    - Attempting to connect to each MCP server
    - Listing available tools
    - Recording success/failure status and tool count
1. **Results Storage**: Test results are saved to `.cache/mcp-test-results.json`
1. **Documentation Update**: The `docs/scripts/generate_mcp_table.py` script generates this markdown file from the template with current test results

### Running Tests Locally

To test MCP servers locally:

```bash
# This will also call target test-mcps
make update-mcps
```

## Contributing

We welcome contributions to expand our MCP server coverage! To add a new MCP server:

1. **Edit the JSON configuration**: Add a new entry to `docs/config/mcp-servers.json` in the `mcpServers` object:
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

2. **Test the server**: Manually trigger the MCP tests workflow to verify your new server works correctly:

   ![MCP Tests Workflow](../assets/mcp-tests-workflow.png)

   To manually trigger the tests:

   1. Go to the [MCP Server Tests workflow](https://github.com/mozilla-ai/agent-factory/actions/workflows/mcp-tests.yaml)
   2. Click the **"Run workflow"** button
   3. Select your branch from the dropdown
   4. Click **"Run workflow"** to start the tests

   The workflow will:
   - Test all MCP servers including your new addition
   - Update the documentation with test results
   - Commit the changes back to your branch

## References

- [Model Context Protocol Documentation](https://modelcontextprotocol.io/)
- [Agent Factory GitHub Repository](https://github.com/mozilla-ai/agent-factory)
