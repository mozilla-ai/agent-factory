# Use an official Python runtime as a parent image
FROM python:3.13-slim

# Set the working directory in the container
WORKDIR /app

# Install uv
RUN pip install uv

# Copy the project files into the container
COPY pyproject.toml uv.lock ./

# Install dependencies using uv
RUN uv sync --no-cache

# Copy the rest of the application code
COPY . /app

# Expose the port the app runs on
EXPOSE 8000

# Run the application
CMD [\
    "uv", "run", "-m", "uvicorn", "backend.main:app", "--reload", \
    "--reload-dir", "/app/backend", \
    "--host", "0.0.0.0", \
    "--port", "8000" \
]
