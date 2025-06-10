from pathlib import Path


def generate_dockerfile(
    base_image: str = "python:3.11-slim",
    workdir: str = "/app",
    requirements_file: str = "requirements.txt",
    entrypoint: str = "agent.py",
    output_path: str = "generated_workflows/latest/Dockerfile",
    include_tools: bool = False,
    include_mcps: bool = False,
) -> str:
    """Generate a Dockerfile to run a Python-based agent.

    Args:
        base_image: Base Docker image to use (default: python:3.11-slim)
        workdir: Working directory inside the container (default: /app)
        requirements_file: Name of the requirements file (default: requirements.txt)
        entrypoint: Name of the Python file to execute (default: agent.py)
        output_path: File path where the Dockerfile will be saved
        include_tools: Whether to include the tools directory (default: False)
        include_mcps: Whether to include the mcps directory (default: False)

    Returns:
        A message indicating where the Dockerfile was saved.
    """
    # Build the Dockerfile content with proper paths for root build context
    dockerfile_content = f"""FROM {base_image}

# Set working directory
WORKDIR {workdir}

# Copy and install requirements
COPY generated_workflows/latest/{requirements_file} ./
RUN pip install --no-cache-dir -r {requirements_file}

# Copy the agent script
COPY generated_workflows/latest/{entrypoint} ./
"""

    # Add optional directories if needed
    if include_tools:
        dockerfile_content += """
# Copy tools directory (if needed by the agent)
COPY tools/ ./tools/"""

    if include_mcps:
        dockerfile_content += """
# Copy MCPs directory (if needed by the agent)
COPY mcps/ ./mcps/"""

    # Add final configuration
    dockerfile_content += f"""
# Create the directory structure the agent expects for trace output
RUN mkdir -p generated_workflows/latest

# Set environment variable to prevent Python buffering
ENV PYTHONUNBUFFERED=1

# Default command
CMD ["python", "{entrypoint}"]
"""

    # Create build instructions comment
    build_instructions = f"""# Build instructions:
# From the project root directory, run:
# docker build -f generated_workflows/latest/Dockerfile -t my-agent .
#
# Run instructions:
# docker run --rm --env-file generated_workflows/latest/.env my-agent
#
# Or with arguments:
# docker run --rm --env-file generated_workflows/latest/.env my-agent python {entrypoint} "your-arguments"

"""

    final_dockerfile = build_instructions + dockerfile_content

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(final_dockerfile)

    return f"Dockerfile generated successfully at {output_path.resolve()}"


def generate_dockerfile_with_auto_detection(
    base_image: str = "python:3.11-slim",
    workdir: str = "/app",
    requirements_file: str = "requirements.txt",
    entrypoint: str = "agent.py",
    output_path: str = "generated_workflows/latest/Dockerfile",
    agent_code: str = "",
) -> str:
    """Generate a Dockerfile with automatic detection of whether tools/mcps are needed.

    Args:
        agent_code: The generated agent code to analyze for dependencies
        (other args same as generate_dockerfile)

    Returns:
        A message indicating where the Dockerfile was saved.
    """
    # Analyze agent code to determine if tools/mcps are needed
    include_tools = "from tools." in agent_code or "tools/" in agent_code
    include_mcps = "MCPStdio" in agent_code or "mcps/" in agent_code

    return generate_dockerfile(
        base_image=base_image,
        workdir=workdir,
        requirements_file=requirements_file,
        entrypoint=entrypoint,
        output_path=output_path,
        include_tools=include_tools,
        include_mcps=include_mcps,
    )
