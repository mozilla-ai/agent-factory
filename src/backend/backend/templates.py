README_TEMPLATE = """# <Title of the Project>

<Description of the project>

## Getting Started

- Create a `.env` file in the project root containing:
    ```
    ENV_VAR_NAME=value
    ```
- Install the required dependencies:
    ```bash
    uv sync
    ```
- Run the Agent server:
    ```bash
    uv run ...
    ```

Your Agent server should now be running at `http://localhost:<port>`.
"""


PYPROJECT_TEMPLATE = """[project]
name = "<project_name>"
version = "0.1.0"
description = "<Brief description of the project>"
readme = "README.md"
requires-python = ">=3.11"
dependencies = [
    "any-agent[all,a2a]==0.21.1",
    "a2a-sdk>=0.2.6",
    "python-dotenv>=1.1.0",
    "uvicorn>=0.34.2",
    <Add any additional dependencies here>
]

[tool.hatch.build.targets.wheel]
packages = ["."]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
"""


README_PROMPT = """Based on the following Python code:
```python
{python_code}
```

Fill in the following `README.md` template with the relevant information:
{readme_template}

Your answer should only contain the filled `README.md` template,
without any additional text or explanations. For example:

```markdown
# Content of the README.md file
...
"""


PYPROJECT_PROMPT = """Based on the following Python code:
```python
{python_code}
```

Fill in the following `pyproject.toml` template with the relevant information:
{pyproject_template}

Your answer should only contain the filled `pyproject.toml` template,
without any additional text or explanations. For example:
```toml
# Content of the pyproject.toml file
...
"""
