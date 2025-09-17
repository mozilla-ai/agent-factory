# Post-mortem Agent

## Overview
This agent gathers context about an incident from Notion, Slack, and Monday.com, analyses the data, and publishes a comprehensive post-mortem in the **Post-mortems** Notion page.

### User-Prompt
_"Create a post-mortem report in Notion in a new page post. The report should be based on a user provided incident.  Search through Notion pages, the #marketing-ops Slack Channel, and activity in Monday.com to find out relevent information about the incident.  The final report in Notion should help find the root-cause of the incident and provide relevant analysis and a timelines."_

### Environment Variables
Create a `.env` file in the project root and add:

```
OPENAI_API_KEY=<your_openai_key>
NOTION_API_KEY=<your_notion_api_key>
SLACK_BOT_TOKEN=<your_slack_bot_token>
SLACK_TEAM_ID=<your_slack_team_id>
MONDAY_API_TOKEN=<your_monday_api_token>
```

### Install `uv` (package manager)

*MacOS/Linux*
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

*Windows*
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

## Run the Agent
```bash
uv run --with-requirements requirements.txt --python 3.13 python agent.py --incident_description "Promo Code Error Launch Campaign"
```
