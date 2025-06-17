from loguru import logger

from agent_factory.instructions import AMENDMENT_PROMPT, TOOLS_REMINDER, USER_PROMPT


class UserPrompt:
    """Singleton class to manage user prompts for agentic workflows.

    This class ensures that only one instance of the user prompt exists.
    The first time it is instantiated, it initializes with a task description. This is the main task
    that the agent will perform.

    Subsequent instantiations will return the same instance, allowing the task description to be
    amended without creating a new instance. This is useful for a multi-step workflow where the user
    may want to refine the result without starting over.

    Attributes:
        task (str): The task description for the agentic workflow.
    """

    _instance = None

    def __new__(cls, task: str):
        if cls._instance is None:
            logger.info("Creating and initializing a new UserPrompt instance...")
            # Create the instance
            instance = super().__new__(cls)
            # Store the task description
            instance.task = task  # type: ignore
            cls._instance = instance

        return cls._instance

    def get_prompt(self) -> str:
        """Return the formatted prompt with the task description.

        Returns:
            str: The formatted prompt string with the task description.
        """
        logger.info("Generating user prompt...")
        return USER_PROMPT.format(self.task, TOOLS_REMINDER)  # type: ignore

    def amend_prompt(self, amendment: str) -> str:
        """Update the task description for the prompt.

        Args:
            amendment (str): The new task description to update.

        Returns:
            str: The updated prompt string with the new task description.
        """
        logger.info("Updating user prompt task description...")
        return AMENDMENT_PROMPT.format(amendment, TOOLS_REMINDER)
