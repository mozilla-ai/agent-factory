.PHONY: help build run run-detached stop clean wait-for-server test-single-turn-generation test-single-turn-generation-local test-single-turn-generation-e2e test-unit test-generated-artifacts test-mcps update-docs docs-serve docs-build

# ====================================================================================
# Configuration
# ====================================================================================
# Load .env if it exists to allow assignment for defaults.
-include .env
export
# Default environment variables for the container if missing.
FRAMEWORK ?= openai
MODEL ?= o3
MAX_TURNS ?= 40
A2A_SERVER_HOST ?= 0.0.0.0
A2A_SERVER_PORT ?= 8080
LOG_LEVEL ?= info
CHAT ?= 0
MCPD_VERSION ?= v0.0.6

# Docker Configuration
DOCKER_IMAGE := agent-factory
DOCKER_CONTAINER := agent-factory-a2a
DOCKER_TAG := latest
DOCKER_RUN_ARGS = --rm \
		--name $(DOCKER_CONTAINER) \
		-p $(A2A_SERVER_PORT):$(A2A_SERVER_PORT) \
		--env-file .env \
		-v $(shell pwd)/traces:/traces \
		-e MCPD_VERSION=$(MCPD_VERSION) \
		-e FRAMEWORK=$(FRAMEWORK) \
		-e MODEL=$(MODEL) \
		-e MAX_TURNS=$(MAX_TURNS) \
		-e A2A_SERVER_HOST=$(A2A_SERVER_HOST) \
		-e A2A_SERVER_PORT=$(A2A_SERVER_PORT) \
		-e LOG_LEVEL=$(LOG_LEVEL) \
		-e CHAT=$(CHAT) \
		$(DOCKER_IMAGE):$(DOCKER_TAG)


# ====================================================================================
# Help Target
# ====================================================================================
.DEFAULT_GOAL := help
help: ## Display this help message
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "%-40s %s\n", $$1, $$2}' $(MAKEFILE_LIST)


# ====================================================================================
# Docker Lifecycle
# ====================================================================================

build: ## Build the Docker image for the server
	@docker build \
		--build-arg APP_VERSION=$(shell git describe --tags --dirty 2>/dev/null || echo "0.1.0.dev0") \
		--build-arg MCPD_VERSION=$(MCPD_VERSION) \
		-t $(DOCKER_IMAGE):$(DOCKER_TAG) \
		.

check-env:
	@if [ ! -f .env ]; then \
		echo "Error: .env file not found. Please create one with your API keys."; \
		exit 1; \
	fi

run: build check-env ## Run the server interactively in the foreground
	@echo "Starting server interactively on http://$(A2A_SERVER_HOST):$(A2A_SERVER_PORT)"
	@docker run $(DOCKER_RUN_ARGS)


run-detached: build check-env ## Run the server in the background (detached mode)
	@echo "Starting server in detached mode..."
	@docker run -d $(DOCKER_RUN_ARGS)


stop: ## Stop the running Docker container
	@if [ "$$(docker ps -q -f name=$(DOCKER_CONTAINER))" ]; then \
		echo "Stopping $(DOCKER_CONTAINER) container..."; \
		docker stop $(DOCKER_CONTAINER); \
	else \
		echo "No $(DOCKER_CONTAINER) container running."; \
	fi

clean: stop # Remove Docker containers and images
	@rm -rf bin && echo "Successfully removed mcpd binaries"
	@docker rmi $(DOCKER_IMAGE):$(DOCKER_TAG) && echo "Successfully removed $(DOCKER_IMAGE):$(DOCKER_TAG) image"

# ====================================================================================
# Testing
# ====================================================================================

check-prompt-id-present:
	@if [ -z "$(PROMPT_ID)" ]; then \
		echo "Error: PROMPT_ID is required. Usage: make $(MAKECMDGOALS) PROMPT_ID=<prompt-id>"; \
		exit 1; \
	fi

test-unit: ## Run unit tests
	@uv run --group tests pytest -v tests/unit/
	@uv run --group tests pytest -v tests/tools/
	@echo "Unit tests completed successfully!"

wait-for-server:
	@echo -n "Waiting for server at http://$(A2A_SERVER_HOST):$(A2A_SERVER_PORT) to be ready..."
	@count=0; \
	while ! curl -s --fail http://$(A2A_SERVER_HOST):$(A2A_SERVER_PORT)/.well-known/agent.json >/dev/null; \
	do \
		sleep 1; \
		count=$$((count+1)); \
		if [ $$count -ge 30 ]; then \
			echo; \
			echo "Error: Timed out waiting for server to be ready after 30 seconds."; \
			echo "Run 'docker logs $(DOCKER_CONTAINER)' to see server logs for errors."; \
			exit 1; \
		fi; \
		printf "."; \
	done;
	@echo " Server is ready!"

test-single-turn-generation: check-prompt-id-present ## Run single turn generation tests
	@echo "Running single turn generation tests for prompt-id: $(PROMPT_ID) $(UPDATE_ARTIFACTS) ..."
	@uv run --group tests pytest -xvs tests/generation/test_single_turn_generation.py --prompt-id=$(PROMPT_ID) $(UPDATE_ARTIFACTS)

test-single-turn-generation-local: UPDATE_ARTIFACTS=--update-artifacts
test-single-turn-generation-local: check-prompt-id-present ## Run test-single-turn-generation with already running A2A server
	@$(MAKE) wait-for-server
	@$(MAKE) test-single-turn-generation PROMPT_ID=$(PROMPT_ID) UPDATE_ARTIFACTS=$(UPDATE_ARTIFACTS)

test-single-turn-generation-e2e: check-prompt-id-present ## Run all tests in a clean, automated environment (for CI)
	@$(MAKE) stop
	@$(MAKE) run-detached
	@$(MAKE) wait-for-server
	@$(MAKE) test-single-turn-generation PROMPT_ID=$(PROMPT_ID); \
	EXIT_CODE=$$?; \
	echo "Tests finished. Stopping server..."; \
	$(MAKE) stop; \
	exit $$EXIT_CODE

test-generated-artifacts: check-prompt-id-present ## Run artifact validation tests
	@echo "Running artifact validation tests for prompt-id: $(PROMPT_ID)..."
	@uv run --group tests pytest tests/generated_artifacts/ -m artifact_validation --prompt-id=$(PROMPT_ID) -v
	@echo "Artifact validation tests completed successfully!"

test-generated-artifacts-integration: check-prompt-id-present ## Run artifact integration tests
	@echo "Running artifact integration tests for prompt-id: $(PROMPT_ID)..."
	@uv run --group tests pytest tests/generated_artifacts/ -m artifact_integration --prompt-id=$(PROMPT_ID) -v
	@echo "Artifact integration tests completed successfully!"

# ====================================================================================
# MCP Testing and Documentation
# ====================================================================================

test-mcps: ## Run MCP server tests
	@echo "Running MCP server tests..."
	uv run python -m docs.scripts.test_mcp_servers

update-mcps: test-mcps ## Update only the MCP doc with the results of the tests
	@echo "Generating MCP documentation..."
	uv run python -m docs.scripts.generate_mcp_table
	@echo "MCP documentation updated successfully!"

# ====================================================================================
# Documentation
# ====================================================================================

docs-serve: ## Serve documentation locally
	@echo "Starting MkDocs development server..."
	@uv sync --quiet --group docs
	@uv run mkdocs serve

docs-build:
	@echo "Building documentation..."
	@uv sync --quiet --group docs
	@uv run mkdocs build
	@echo "Documentation built successfully!"
