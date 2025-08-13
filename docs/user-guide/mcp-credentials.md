# MCP Credentials

> Put secrets in environment variables or a secrets manager. Don’t commit them to git.

**Quick links:** [Slack](#slack) · [Notion](#notion) · [Mondaycom](#mondaycom) · [GitHub](#github) · [Tavily](#tavily) · [Discord](#discord) · [Salesforce](#salesforce) · [Perplexity](#perplexity) · [Jira](#jira) · [Confluence](#confluence) · [Airtable](#airtable) · [GitLab](#gitlab)


## **Slack**

**Create a `SLACK_BOT_TOKEN`**

1. Open your Slack [API Apps](https://api.slack.com/apps) page.
2. Select Create New App → From scratch.
3. Enter an App Name and choose the Workspace you want to use.
4. Click Create App (the app details page opens).
5. In the left menu under Features, select OAuth & Permissions.
6. In Scopes, select the appropriate scopes for your app.
7. Scroll up to OAuth Tokens and click Install to Workspace (you must be a Slack workspace admin).
8. Select Allow.
9. Copy the Bot User OAuth Token and use it as the `SLACK_BOT_TOKEN`.

**Find your `SLACK_TEAM_ID`**

* Open your workspace in a web browser.
* The team ID is in the URL, usually starts with “T” and is 11 characters long.

**Find your `SLACK_CHANNEL_ID`**

* Open your workspace in a web browser.
* The channel ID is in the URL, usually starts with “C” and is 11 characters long.

## **Notion**

**Create an `INTERNAL_INTEGRATION_TOKEN`**

You can find instructions for getting an `INTERNAL_INTEGRATION_TOKEN` on the [Notion Docs here](https://www.notion.com/help/create-integrations-with-the-notion-api), which will bring you to the [Notion integration](https://www.notion.com/my-integrations) page.

**Create `OPENAPI_MCP_HEADERS`**

1. Copy: `{"Authorization": "Bearer ntn_****", "Notion-Version": "2022-06-28" }`
2. Replace `ntn_****` with your Internal Integration Secret.
3. Enter the text (e.g. `{"Authorization": "Bearer ntn_12345678", "Notion-Version": "2022-06-28" }`) as the `OPENAPI_MCP_HEADERS`.

## **Monday.com**

**Create your `MONDAY_API_TOKEN`**

You can find instructions for getting a `MONDAY_API_TOKEN` on the [Monday.com developer docs here](https://developer.monday.com/api-reference/docs/authentication).

## **GitHub**

**Create a `GITHUB_PERSONAL_ACCESS_TOKEN`**

You can find instructions for getting a `GITHUB_PERSONAL_ACCESS_TOKEN` on the [Github docs here](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens#creating-a-personal-access-token-classic) (follow creating a personal access token **classic**)

## **Tavily**

**Create a `TAVILY_API_KEY`**

You can find instructions on getting a `TAVILY_API_KEY` on the [Tavily docs here](https://docs.tavily.com/documentation/about#getting-started)

## **Discord**

**Create a `DISCORD_BOT_TOKEN`**

1. Create a Discord Application: If you don't have one, create a new application in the [Discord Developer Portal](https://discord.com/developers/applications?new_application=true).
2. Name Your Application: Enter a name for your application and click "Create."
3. Access Bot Settings: From the left menu, select "Bot."
4. Generate Bot Token: Under "Token," click "Reset Token" to generate a new bot token.
5. Copy Token: Copy the generated token and paste it as the `DISCORD_BOT_TOKEN` in your agent configuration. (Ensure the following steps are completed before running the agent.)
6. Configure Privileged Gateway Intents: In "Bot > Privileged Gateway Intents," add any privileged intents your bot requires. Refer to [Configuring your bot](https://discord.com/developers/docs/quick-start/getting-started#configuring-your-bot) for more details.
7. Add Bot Permissions: On the "Bot > Bot Permissions" page, add the necessary permissions. Refer to Discord's [Permissions](https://discord.com/developers/docs/topics/permissions) documentation for more information.
8. Select Installation Contexts: In "Installation > Installation Contexts," choose the installation contexts for your bot. Refer to Discord's [Choosing installation contexts](https://discord.com/developers/docs/quick-start/getting-started#choosing-installation-contexts) documentation for more information.
9. Choose Discord Provided Link: On the "Installation" page, ensure "Discord Provided Link" is selected under "Install Link."
10. Set Default Install Scopes: Still on the "Installation" page, in the "Default Install Settings" section, select `applications.commands` and `bot` scopes.
11. Add App to Your Server:
    1. Go to "Installation > Install Link" and copy the provided link.
    2. Paste the link into your browser and press Enter.
    3. In the installation prompt, select "Add to server."
    4. Once added, your app will appear in the server's member list.

## **Salesforce**

**Create a `SALESFORCE_SECURITY_TOKEN`**

You can find instructions on how to get a `SALESFORCE_SECURITY_TOKEN` by resetting your security token in the [Salesforce Help docs here](https://help.salesforce.com/s/articleView?id=xcloud.user_security_token.htm&type=5_)

## **Perplexity**

**Create a `PERPLEXITY_API_KEY`**

You can find information on how to get a `PERPLEXITY_API_KEY` in the [Perplexity help center here](https://www.perplexity.ai/help-center/en/articles/10352995-api-settings)

## **Jira**

**Create a `JIRA_TOKEN`**

1. Log in to your Atlassian profile, then click Security, then go to the [API tokens page](https://id.atlassian.com/manage-profile/security/api-tokens)
2. Select Create API Token.
3. Enter a Label for your token and then click Create.
4. Copy the API token and use it as the `JIRA_TOKEN`.

**`JIRA_USERNAME`**

This is the email you used to sign-into your Atlassian profile

**`JIRA_URL`**

This is the domain of your atlassian you use to , for example [`https://example.atlassian.net`](https://example.atlassian.net).

## **Confluence**

**Create a `CONFLUENCE_TOKEN`**

5. Log in to your Atlassian profile, then click Security, then go to the [API tokens page](https://id.atlassian.com/manage-profile/security/api-tokens)
6. Select Create API Token.
7. Enter a Label for your token and then click Create.
8. Copy the API token and use it as the `CONFLUENCE_TOKEN`.

**`CONFLUENCE_USERNAME`**

This is the email you used to sign-into your Atlassian profile

**`CONFLUENCE_URL`**

This is the domain of your atlassian you use to , for example [`https://example.atlassian.net/wiki`](https://example.atlassian.net/wiki)

## **Airtable**

**Create a `AIRTABLE_API_KEY`**

You can find instructions on how to create an Airtable personal access token in the [Airtable support docs here](https://support.airtable.com/v1/docs/creating-personal-access-tokens)
Copy the personal accees token you create and use it as the `AIRTABLE_API_KEY`.

## **Gitlab**

**Create a `GITLAB_PERSONAL_ACCESS_TOKEN`**

You can find instructions on how to create a `GITLAB_PERSONAL_ACCESS_TOKEN` on [the Gitlab docs here](https://docs.gitlab.com/user/profile/personal_access_tokens/#create-a-personal-access-token).

**`GITLAB_API_URL`**

Enter: `https://gitlab.com/api/v4`
