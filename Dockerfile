FROM python:3.13-slim

# Set the working directory in the container
WORKDIR /app

ENV FRAMEWORK=openai
# Enable or disable chat mode
# Set to 1 to enable chat mode, 0 to disable
ENV CHAT=1
ENV MODEL=o3
ENV HOST=0.0.0.0
ENV PORT=8080
ENV LOG_LEVEL=info

# Define an argument for the version
ARG APP_VERSION

# Set the environment variable for setuptools_scm
ENV SETUPTOOLS_SCM_PRETEND_VERSION=${APP_VERSION}

# Copy mcpd to the container
COPY --from=mzdotai/mcpd:v0.0.3 /usr/local/bin/mcpd /usr/local/bin/mcpd
RUN chmod +x /usr/local/bin/mcpd

# Install uv
RUN pip install uv

# Copy the rest of the application code
COPY . /app

# Install dependencies using uv
RUN uv sync --no-cache

# Set the working directory
WORKDIR /app/src/agent_factory

# Expose the port the app runs on
EXPOSE 8000

# Create startup script
RUN chmod +x start.sh

# Run the application
CMD ["./start.sh"]
