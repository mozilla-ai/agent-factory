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

1. Go to your [Notion integration](https://www.notion.com/my-integrations) page.
2. Click + New integration.
3. Enter a Name (e.g., *agent integration*).
4. Select Submit to create your integration.
5. Under Capabilities, select the required capabilities (e.g.):
   * Read content
   * Update content
   * Insert content
6. Be sure to Save changes.
7. Copy the Internal Integration Secret (starts with `ntn_`) and use it as the `INTERNAL_INTEGRATION_TOKEN`.

**Create `OPENAPI_MCP_HEADERS`**

1. Copy: `{"Authorization": "Bearer ntn_****", "Notion-Version": "2022-06-28" }`
2. Replace `ntn_****` with your Internal Integration Secret.
3. Enter the text (e.g. `{"Authorization": "Bearer ntn_12345678", "Notion-Version": "2022-06-28" }`) as the `OPENAPI_MCP_HEADERS`.

## **Monday.com**

**Create your `MONDAY_API_TOKEN`**

1. In your monday.com account, click your profile picture (top right).
2. Select Developers (the Developer Center opens).
3. In the Developer Center, select API Token.
4. Copy your API token and use it as `MONDAY_API_TOKEN`.

## **GitHub**

**Create a `GITHUB_PERSONAL_ACCESS_TOKEN`**

1. Ensure your Github email is verified. See [Verifying your email address](https://docs.github.com/en/account-and-profile/setting-up-and-managing-your-personal-account-on-github/managing-email-preferences/verifying-your-email-address) for more information.
2. Open your GitHub profile [Settings](https://github.com/settings/profile).
3. In the left side bar, select [Developer settings](https://github.com/settings/apps).
4. In the left side bar, under Personal access tokens, select Tokens (classic).
5. Select Generate new token, then Generate new token (classic)..
6. Select the Expiration you'd like for the token
7. Select Scopes for your token (a token without assigned scopes can only access public information)
8. Select Generate token.
9. Copy the token and use it as the `GITHUB_PERSONAL_ACCESS_TOKEN`.

## **Tavily**

**Create a `TAVILY_API_KEY`**

1. Log-into [Tavily](https://www.tavily.com/)
2. Navigate to [app.tavily](https://app.tavily.com/home)
3. Click on the ‘+’ under ‘API Keys’
4. Under a key name, select key type (e.g. development)
5. Copy the key and use it as the `TAVILY_API_KEY`.


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

1. Sign-into Salesforce
2. In the top right corner, click your user icon, then select "Settings".
3. In the left-hand menu, under "My Personal Information", click "Reset My Security Token".
4. Click "Reset Security Token"
5. Salesforce will send the new token to your registered email address.
6. Copy the key and use it as the `SALESFORCE_SECURITY_TOKEN`.

## **Perplexity**

**Create a `PERPLEXITY_API_KEY`**

1. [Sign-into Perplexity](https://www.perplexity.ai/)
2. Go to your [accounts details](https://www.perplexity.ai/account/details)
3. Click on API and create a new API Group
4. Enter your payment details if required
5. Click ‘Create key’ and copy the key and use it as the `PERPLEXITY_API_KEY`.

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

1. Go to the Airtable Builder Hub [Personal access tokens](https://airtable.com/create/tokens) page.
2. Select + Create new token.
3. Enter an appropriate name for your token
4. Add Scopes to your token. Refer to Airtable's [Scopes](https://airtable.com/developers/web/api/scopes) guide for more information. Example scopres
   * `data.records:read`
   * `data.records:write`
   * `schema.bases:read`
5. Select the Access for your token. Choose from a single base or all of the bases from any workspace that you own
6. Click create token
7. Copy this token and use it as the `AIRTABLE_API_KEY`.

## **Gitlab**

**Create a `GITLAB_PERSONAL_ACCESS_TOKEN`**

1. In GitLab, select your avatar, then select Edit profile.
2. In the left sidebar, select Access tokens.
3. Select Add new token.
4. Enter a Name for the token
5. Enter an expiry date for the token
6. Select the desired Scopes. Refer to [Personal access token scopes](https://docs.gitlab.com/ee/user/profile/personal_access_tokens.html#personal-access-token-scopes) to select scopes for the functions you want to use.
7. Select Create personal access token.
8. Copy the token and use it as the `GITLAB_PERSONAL_ACCESS_TOKEN`

**`GITLAB_API_URL`**

Enter: `https://gitlab.com/api/v4`
