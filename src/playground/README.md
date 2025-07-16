# Chainlit Playground

This directory contains a Chainlit application that serves as a playground for interacting with the Agent Factory. It provides a user-friendly interface to chat with the agent, view the generated responses, and save the resulting agent code locally.

## Prerequisites

- Python 3.11+
- [uv](https://github.com/astral-sh/uv)

## Installation

1.  Navigate to the playground's source directory:
    ```bash
    cd src/playground
    ```

2.  Install the dependencies using `uv`:
    ```bash
    uv sync
    ```

3.  Activate the virtual environment:
    ```bash
    source .venv/bin/activate
    ```

## Running the Application

1.  **Start the Agent Factory Server:** Before running the playground, ensure that the Agent Factory server from the `src/agent` directory is running. You can follow the instructions in `src/agent/README.md` to start it.

2.  **Run the Chainlit App:** With the agent server running, start the Chainlit application from the `src/playground` directory:
    ```bash
    chainlit run playground.py -w
    ```
    The `-w` flag enables auto-reloading, which is useful for development.

3.  **Access the Playground:** Open your web browser and navigate to `http://localhost:8000` (or the address provided in the terminal).
