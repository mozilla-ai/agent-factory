# Define build args at the top for the mcpd stage
ARG MCPD_VERSION=v0.0.6

# Stage to pull mcpd binary
FROM mzdotai/mcpd:${MCPD_VERSION} AS mcpd

# Main application stage
FROM python:3.13-slim

# Set the working directory in the container
WORKDIR /app

ENV FRAMEWORK=tinyagent
# Enable or disable chat mode
# Set to 1 to enable chat mode, 0 to disable
ENV CHAT=1
ENV MODEL=openai:o3
ENV MAX_TURNS=40
ENV A2A_SERVER_HOST=0.0.0.0
ENV A2A_SERVER_PORT=8080
ENV LOG_LEVEL=info
ENV TRACES_DIR=/traces

# Create and set permissions for the traces directory
RUN mkdir -p ${TRACES_DIR} && \
    chmod 777 ${TRACES_DIR}

# Define an argument for the version
ARG APP_VERSION

# Set the environment variable for setuptools_scm
ENV SETUPTOOLS_SCM_PRETEND_VERSION=${APP_VERSION}

# Copy mcpd from the mcpd stage
COPY --from=mcpd /usr/local/bin/mcpd /usr/local/bin/mcpd
RUN chmod +x /usr/local/bin/mcpd

# Install uv
COPY --from=ghcr.io/astral-sh/uv:0.8.4 /uv /uvx /usr/local/bin/

# Copy application code and required project assets.
COPY pyproject.toml /app
COPY uv.lock /app
COPY src /app/src

# Install dependencies using uv
RUN uv sync --no-cache --locked --no-editable --no-dev
RUN rm -rf /app/build

# Set the working directory
WORKDIR /app/src/agent_factory

# Expose the port the app runs on
EXPOSE 8000

# Create startup script
RUN chmod +x start.sh

# Run the application
CMD ["./start.sh"]
