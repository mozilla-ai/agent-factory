# Newsletter

<details>
  <summary>Prompt</summary>

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

</details>
