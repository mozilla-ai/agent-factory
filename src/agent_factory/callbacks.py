from any_agent.callbacks import Callback, Context


class LimitAgentTurns(Callback):
    def __init__(self, max_turns: int):
        self.max_turns = max_turns

    def before_llm_call(self, context: Context, *args, **kwargs) -> Context:
        if "n_agent_turns" not in context.shared:
            context.shared["n_agent_turns"] = 0
        context.shared["n_agent_turns"] += 1
        if context.shared["n_agent_turns"] > self.max_turns:
            raise RuntimeError(f"Reached limit of agent turns: {self.max_turns}")
        return context
