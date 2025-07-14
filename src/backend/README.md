# Agent Factory Backend

Agent Factory Backend is a **FastAPI application** that provides the backend services for Agent Factory. It handles agent creation, management, and communication with the Agent Factory agent.

## Key Capabilities

* **Agent Management:** Create, retrieve, and manage agents.
* **Task Queueing:** Uses Celery and Redis to manage long-running tasks, such as agent creation and message passing.
* **Database:** Uses SQLAlchemy to store agent information.

## Getting Started

### Prerequisites

- Python 3.13+
- [uv](https://github.com/astral-sh/uv)
- Docker (for running Redis)
- Redis

### Installation

1. Clone the repository and navigate to the backend's source directory:
   ```bash
   git clone https://github.com/mozilla-ai/agent-factory.git
   cd agent-factory/src/backend
   ```

2. Install the dependencies using `uv`:
   ```bash
   uv sync
   ```

3. Activate the virtual environment:
   ```bash
   source .venv/bin/activate
   ```

### Running the Application Locally

1. **Run the Agent:** Follow the instructions in the [Agent Factory README](../agent/README.md) to run the Agent
   Factory agent.

2. **Start Redis:**
   You need a Redis server running on `localhost:6379`. You can start one using Docker:
   ```bash
   docker run -d -p 6379:6379 redis
   ```

3. **Run the FastAPI Application:**
   Navigate back to the `src/backend` directory and run the FastAPI application:
   ```bash
   uvicorn backend.main:app --reload
   ```
   The application will be available at `http://localhost:8000`.

4. **Run the Celery Worker:**
   In another separate terminal, run the Celery worker from the `src/backend` directory:
   ```bash
   celery -A backend.celery_app worker --loglevel=info
   ```

#### Using Docker Compose

From the root of the project, you can use Docker Compose to run the entire application stack, including the Agent, the
FastAPI application, the Celery worker, and the Redis broker.

```bash
docker-compose up
```

This will start all the services defined in the `docker-compose.yaml` file.

To stop the application, run:

```bash
docker-compose down
```
