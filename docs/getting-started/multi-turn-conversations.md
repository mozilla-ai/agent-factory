## Multi-Turn Conversations

Agent Factory supports multi-turn conversations. You can run the Chainlit application to interact with the Agent server
in a conversational manner:

```bash
A2A_SERVER_PORT=8080 uv run chainlit run src/agent_factory/chainlit.py
```
> [!NOTE]
> If you are running the server on a different port, you need to set the `A2A_SERVER_PORT` environment variable accordingly.
