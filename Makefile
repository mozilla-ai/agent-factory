.PHONY: help build run run-detached stop clean wait-for-server test-single-turn-generation test-single-turn-generation-local test-single-turn-generation-e2e

#est-local test

# ====================================================================================
# Configuration
# ====================================================================================
DOCKER_IMAGE := agent-factory
DOCKER_CONTAINER := agent-factory-a2a
DOCKER_TAG := latest

# Server Configuration
A2A_SERVER_HOST ?= localhost
A2A_SERVER_LOCAL_PORT ?= 8080

# Default environment variables for the container
FRAMEWORK ?= openai
MODEL ?= o3
HOST ?= 0.0.0.0
PORT ?= 8080
LOG_LEVEL ?= info
CHAT ?= 0

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
	@docker build --build-arg APP_VERSION=$(shell git describe --tags --dirty 2>/dev/null || echo "0.1.0.dev0") -t $(DOCKER_IMAGE):$(DOCKER_TAG) .

run: build ## Run the server interactively in the foreground
	@if [ ! -f .env ]; then \
		echo "Error: .env file not found. Please create one with your API keys."; \
		exit 1; \
	fi
	@echo "Starting server interactively on http://$(A2A_SERVER_HOST):$(A2A_SERVER_LOCAL_PORT)"
	@docker run --rm \
		--name $(DOCKER_CONTAINER) \
		-p $(A2A_SERVER_LOCAL_PORT):8080 \
		--env-file .env \
		-e FRAMEWORK=$(FRAMEWORK) \
		-e MODEL=$(MODEL) \
		-e HOST=$(HOST) \
		-e PORT=$(PORT) \
		-e LOG_LEVEL=$(LOG_LEVEL) \
		-e CHAT=$(CHAT) \
		$(DOCKER_IMAGE):$(DOCKER_TAG)

run-detached: build ## Run the server in the background (detached mode)
	@if [ ! -f .env ]; then \
		echo "Error: .env file not found. Please create one with your API keys."; \
		exit 1; \
	fi
	@echo "Starting server in detached mode..."
	@docker run -d --rm \
		--name $(DOCKER_CONTAINER) \
		-p $(A2A_SERVER_LOCAL_PORT):8080 \
		--env-file .env \
		-e FRAMEWORK=$(FRAMEWORK) \
		-e MODEL=$(MODEL) \
		-e HOST=$(HOST) \
		-e PORT=$(PORT) \
		-e LOG_LEVEL=$(LOG_LEVEL) \
		-e CHAT=$(CHAT) \
		$(DOCKER_IMAGE):$(DOCKER_TAG)

stop: ## Stop the running Docker container
	@if [ "$$(docker ps -q -f name=$(DOCKER_CONTAINER))" ]; then \
		echo "Stopping $(DOCKER_CONTAINER) container..."; \
		docker stop $(DOCKER_CONTAINER); \
	else \
		echo "No $(DOCKER_CONTAINER) container running."; \
	fi

clean: stop ## Remove the Docker image
	@docker rmi $(DOCKER_IMAGE):$(DOCKER_TAG)
	@echo "Successfully removed $(DOCKER_IMAGE):$(DOCKER_TAG) image"

# ====================================================================================
# Testing
# ====================================================================================
wait-for-server:
	@echo -n "Waiting for server at http://$(A2A_SERVER_HOST):$(A2A_SERVER_LOCAL_PORT) to be ready..."
	@count=0; \
	while ! curl -s --fail http://$(A2A_SERVER_HOST):$(A2A_SERVER_LOCAL_PORT)/.well-known/agent.json >/dev/null; \
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

test-single-turn-generation:
	@if [ -z "$(PROMPT_ID)" ]; then \
		echo "Error: PROMPT_ID is required. Usage: make test-single-turn-generation PROMPT_ID=<prompt-id> [UPDATE_ARTIFACTS=--update-artifacts]"; \
		exit 1; \
	fi
	@echo "Running single turn generation tests for prompt-id: $(PROMPT_ID) $(UPDATE_ARTIFACTS) ..."
	@uv sync --quiet --group tests
	@pytest -xvs tests/generation/test_single_turn_generation.py --prompt-id=$(PROMPT_ID) $(UPDATE_ARTIFACTS)

test-single-turn-generation-local: UPDATE_ARTIFACTS=--update-artifacts
test-single-turn-generation-local: ## Run test-single-turn-generation with already running A2A server
	@$(MAKE) wait-for-server
	@$(MAKE) test-single-turn-generation PROMPT_ID=$(PROMPT_ID) UPDATE_ARTIFACTS=$(UPDATE_ARTIFACTS)

test-single-turn-generation-e2e: ## Run all tests in a clean, automated environment (for CI)
	@$(MAKE) stop
	@$(MAKE) run-detached
	@$(MAKE) wait-for-server
	@$(MAKE) test-single-turn-generation PROMPT_ID=$(PROMPT_ID); \
	EXIT_CODE=$$?; \
	echo "Tests finished. Stopping server..."; \
	$(MAKE) stop; \
	exit $$EXIT_CODE
