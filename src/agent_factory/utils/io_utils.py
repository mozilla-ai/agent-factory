import ast
import importlib.metadata
import sys
from pathlib import Path

from agent_factory.instructions import AGENT_CODE_TEMPLATE
from agent_factory.schemas import AgentParameters
from agent_factory.utils import prepare_python_code, validate_dependencies
from agent_factory.utils.logging import logger
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


def get_imports_from_string(code_string):
    """Parses a Python code string and returns a set of imported module names.

    Args:
        code_string (str): The Python code to analyze.

    Raises:
        SyntaxError: If the code_string is not valid Python code.
    """
    try:
        tree = ast.parse(code_string)
    except SyntaxError as e:
        logger.error(f"Error parsing code string: {e}")
        raise

    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                # For statements like 'import pandas' or 'import pandas.DataFrame'
                imports.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            # For 'from collections import deque', module is 'collections'
            # level 0 means it's not a relative import
            if node.module and node.level == 0:
                imports.add(node.module.split(".")[0])
    return imports


def extract_requirements_from_string(python_code: str) -> set[str]:
    """Extract dependencies from a string of Python code.

    Analyze a string of Python code, filter out standard library modules, and extract the third-party imports.

    Args:
        python_code (str): The Python code to analyze.
    """
    stdlib = set(sys.stdlib_module_names)
    all_imports = get_imports_from_string(python_code)
    third_party_imports = sorted(list(all_imports - stdlib))

    if "tools" in third_party_imports:
        third_party_imports.remove("tools")

    logger.info("Mapping import names to their corresponding package names...")
    # packages_distributions() returns a mapping of top-level modules to the
    # distribution (installable) package names that provide them.
    # e.g., {'bs4': ['beautifulsoup4'], 'sklearn': ['scikit-learn']}
    try:
        dist_map = importlib.metadata.packages_distributions()
    except Exception as e:
        print(f"Could not get package distributions: {e}")
        print("Falling back to using import names directly.")
        dist_map = {}

    final_packages = set()
    for imp in third_party_imports:
        if imp in dist_map:
            package_name = dist_map[imp][0]
            final_packages.add(package_name)
            logger.info(f"Mapped import '{imp}' to package '{package_name}'")
        else:
            final_packages.add(imp)
            logger.info(f"Could not find a package map for '{imp}', using it directly.")

    return final_packages


def prepare_agent_artifacts(agent_factory_outputs: dict[str, str]) -> dict[str, str]:
    """Prepares the agent outputs (based on AgentFactoryOutputs)
    for saving by filling in the code generation templates
    and gathering (Python) tool files.
    """
    artifacts_to_save = {}

    agent_code = AGENT_CODE_TEMPLATE.format(**agent_factory_outputs)
    valid_agent_code = prepare_python_code(agent_code)
    artifacts_to_save["agent.py"] = valid_agent_code.code

    artifacts_to_save["README.md"] = agent_factory_outputs["readme"]

    dependencies = set()
    # Identify and read tool files
    for tool_file in TOOLS_DIR.iterdir():
        if tool_file.is_file() and (tool_file.stem in agent_code or tool_file.name == "__init__.py"):
            if tool_file.suffix != ".py":
                continue
            tool_code = tool_file.read_text(encoding="utf-8")
            dependencies.update(extract_requirements_from_string(tool_code))
            artifacts_to_save[f"tools/{tool_file.name}"] = tool_code

    dependencies.update(extract_requirements_from_string(valid_agent_code.code))  # type: ignore
    dependencies_list = list(dependencies)
    validated_dependencies = validate_dependencies(agent_factory_outputs["tools"], dependencies_list)
    artifacts_to_save["requirements.txt"] = validated_dependencies

    cli_args_str = agent_factory_outputs.get("cli_args", "")
    artifacts_to_save["agent_parameters.json"] = parse_cli_args_to_params_json(cli_args_str)

    mcpd_artifacts = export_mcpd_config_artifacts(agent_factory_outputs)
    artifacts_to_save.update(mcpd_artifacts)

    # Add a .gitignore file for ignoring secrets
    artifacts_to_save[".gitignore"] = "*secrets*.dev.toml\n!secrets.prod.toml"

    return artifacts_to_save
