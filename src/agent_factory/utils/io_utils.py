from pathlib import Path

from agent_factory.instructions import AGENT_CODE_TEMPLATE
from agent_factory.schemas import AgentParameters
from agent_factory.utils import clean_python_code_with_autoflake, validate_dependencies
from agent_factory.utils.mcpd_utils import export_mcpd_config_artifacts

TOOLS_DIR = Path(__file__).parent.parent / "tools"


def parse_cli_args_to_params_json(cli_args_str: str) -> str:
    """Parse CLI arguments into the schema format the platform expects
    Example: "url: str" -> {"params": {"--url": "string"}}
    """
    params_dict = {}
    if cli_args_str:
        for arg in cli_args_str.split(","):
            arg = arg.strip()
            if ":" in arg:
                name, arg_type = arg.split(":", 1)
                name = name.strip()
                arg_type = arg_type.strip()
                param_name = f"--{name}"

                if arg_type == "str":
                    param_type = "string"
                elif arg_type == "int":
                    param_type = "integer"
                elif arg_type == "float":
                    param_type = "number"
                elif arg_type == "bool":
                    param_type = "boolean"
                else:
                    param_type = "string"
                params_dict[param_name] = param_type

    agent_parameters = AgentParameters(params=params_dict)
    return agent_parameters.model_dump_json()


def prepare_agent_artifacts(agent_factory_outputs: dict[str, str]) -> dict[str, str]:
    """Prepares the agent outputs (based on AgentFactoryOutputs)
    for saving by filling in the code generation templates
    and gathering (Python) tool files.
    """
    artifacts_to_save = {}
    agent_code = AGENT_CODE_TEMPLATE.format(**agent_factory_outputs)
    clean_agent_code = clean_python_code_with_autoflake(agent_code)
    validated_dependencies = validate_dependencies(agent_factory_outputs)

    artifacts_to_save["agent.py"] = clean_agent_code
    artifacts_to_save["README.md"] = agent_factory_outputs["readme"]
    artifacts_to_save["requirements.txt"] = validated_dependencies

    # Identify and read tool files
    for tool_file in TOOLS_DIR.iterdir():
        if tool_file.is_file() and (tool_file.stem in agent_code or tool_file.name == "__init__.py"):
            artifacts_to_save[f"tools/{tool_file.name}"] = tool_file.read_text(encoding="utf-8")

    cli_args_str = agent_factory_outputs.get("cli_args", "")
    artifacts_to_save["agent_parameters.json"] = parse_cli_args_to_params_json(cli_args_str)

    mcpd_artifacts = export_mcpd_config_artifacts(agent_factory_outputs)
    artifacts_to_save.update(mcpd_artifacts)

    # Add a .gitignore file for ignoring secrets
    artifacts_to_save[".gitignore"] = "*secrets*.dev.toml\n!secrets.prod.toml"

    return artifacts_to_save
