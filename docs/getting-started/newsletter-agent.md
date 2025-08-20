# Use-case: Newsletter Agent

This guide highlights the use-case of using an AI agent to automate the newsletter creation process, gathering the latest news articles from web sources and generating a comprehensive newsletter in multiple formats.

Specifically, we will be using the following tools to gather and distribute content:
- **Tavily** (for web search and article discovery)
- **Web browsing** (for reading and summarizing articles)
- **Slack** (optional, for newsletter distribution)

The agent will generate a newsletter in your preferred format (HTML, PDF, or Markdown) and optionally post it to a specified Slack channel.

## Building our Agent

### 1. Start the Agent Factory Server

Let's use [Docker](https://www.docker.com/products/docker-desktop) to run the Agent Factory server. Make sure we have Docker Desktop installed and running, then run the Makefile command to start the server:

```bash
make run
```
After docker has set up the server, we can verify that is up and running at `http://localhost:8080/.well-known/agent.json`.

### 2. Send our Prompt to the Manufacturing Agent

We can now send a request to the Agent Factory server to generate our newsletter agent. In a terminal, run the following command:

```bash
uv run agent-factory 'Create an agent that creates a newsletter based on the latest news articles from topics defined by the user. Specifically, the agent should:

1. Take as input from the user:
- keywords / topics (required)
- number of articles to include in the newsletter (optional, default to 5)
- newsletter title (optional, default to "Latest News on {keywords}")
- sources for articles, which can be a list of URLs or specific news outlets (optional, default to None, which means whichever sources are available through the web search)
- date range for the articles (optional, default to last 7 days)
- export format (optional, multiple options can be selected out of: "pdf", "html", "markdown", default to "html")
- slack channel to post the newsletter (optional, default to None)

2. Searches the web with Tavily for the latest news articles related to those topics, according to the user-defined parameters.

3. Visit the web pages, read through the articles and summarize each one, extracting key points and relevant information.

4. Assemble the summaries into a newsletter format, including:
- Title
- Date
- List of articles with summaries
- Links to the full articles

5. Export the newsletter in the requested format(s)

6. If the user provided a Slack channel, post the newsletter to that channel.'
```


### 3. Inspect the Target Agent and its requirements

First, let's inspect the generated README.md of the target agent to understand its requirements and how to run it.

We see that the agent requires some environment variables and positional arguments for the newsletter topics.

> [!NOTE]
> We can also inspect if our Target Agent requires any positional arguments by running:
> ```bash
> uv run --with-requirements requirements.txt --python 3.13 python agent.py --help
> ```

### 4. Fill in the necessary environment variables

Create a `.env` file in the directory of the target agent and add environment variables as instructed in the README.md file with the credentials we set up earlier.

For example:
```bash
TAVILY_API_KEY=<your_tavily_api_key>
MCPD__SLACK_MCP__SLACK_BOT_TOKEN=<your_slack_bot_token>
MCPD__SLACK_MCP__SLACK_TEAM_ID=<your_slack_team_id>
```

### 5. Start the mcpd daemon

Now we need to start up [mcpd](https://github.com/mozilla-ai/mcpd), which will start up the local MCP servers of our tools. We are also going to be exporting the environment variables from our `.env` file to make them available to the mcpd daemon.

```bash
export $(cat .env | xargs) &&  mcpd daemon --log-level=DEBUG --log-path=$(pwd)/mcpd.log --dev --runtime-file secrets.prod.toml
```

### 6. Run the Agent

As indicated by the README.md of the newsletter agent, we can now run the agent with the following command:

```bash
uv run --with-requirements requirements.txt --python 3.13 python agent.py --keywords "open source agentic AI" --num_articles 3 --export_formats "html,markdown,pdf" --slack_channel "#newsletter"
```

### 7. Verify that it worked

After the above command is complete, we can verify that the agent has successfully created a newsletter by checking:

1. **Local files**: The newsletter will be saved in the specified format(s) in the current directory
2. **Slack channel**: If a Slack channel was specified, the newsletter will be posted there
3. **Console output**: The agent will display a summary of the articles found and processed

<details>
<summary>Example of a generated newsletter</summary>

</details>

Now, any time you want to create a newsletter on different topics, you can simply run this agent with different parameters to generate a new newsletter tailored to your interests.
  <summary>Prompt</summary>
