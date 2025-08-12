.PHONY: help prepare build run run-detached stop clean wait-for-server test-single-turn-generation test-single-turn-generation-local test-single-turn-generation-e2e test-unit test-generated-artifacts test-mcps update-docs docs-serve docs-build

# ====================================================================================
# Configuration
# ====================================================================================
# Default environment variables for the container
FRAMEWORK ?= openai
MODEL ?= o3
HOST ?= 0.0.0.0
PORT ?= 8080
LOG_LEVEL ?= info
CHAT ?= 0

# Docker Configuration
DOCKER_IMAGE := agent-factory
DOCKER_CONTAINER := agent-factory-a2a
DOCKER_TAG := latest

# MCPD Configuration
MCPD_VERSION ?= $(shell curl -s https://api.github.com/repos/mozilla-ai/mcpd/releases/latest | jq -r .tag_name)
MCPD_ARCH ?= $(shell uname -m)
MCPD_TAR = mcpd_Linux_$(MCPD_ARCH).tar.gz
MCPD_URL = https://github.com/mozilla-ai/mcpd/releases/download/$(MCPD_VERSION)/$(MCPD_TAR)
MCPD_BIN_PATH = bin
MCPD_BASE_NAME = mcpd
MCPD_BIN_PATH_BASE=$(MCPD_BIN_PATH)/$(MCPD_BASE_NAME)
MCPD_BIN_PATH_ARCH=$(MCPD_BIN_PATH)/$(MCPD_BASE_NAME)_$(MCPD_ARCH)

# Server Configuration
A2A_SERVER_HOST ?= localhost
A2A_SERVER_LOCAL_PORT ?= 8080


# ====================================================================================
# Help Target
# ====================================================================================
.DEFAULT_GOAL := help
help: ## Display this help message
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "%-40s %s\n", $$1, $$2}' $(MAKEFILE_LIST)


# ====================================================================================
# Docker Lifecycle
# ====================================================================================

prepare: ## Prepare mcpd binary for Docker container
	@mkdir -p bin
	@if [ ! -f $(MCPD_BIN_PATH_ARCH) ]; then \
		echo "Downloading mcpd binary for $(MCPD_ARCH)..."; \
		curl -sSL $(MCPD_URL) -o "$(MCPD_BIN_PATH)/$(MCPD_TAR)"; \
		tar -xzf $(MCPD_BIN_PATH)/$(MCPD_TAR) $(MCPD_BASE_NAME); \
		mv mcpd $(MCPD_BIN_PATH_ARCH); \
		chmod +x $(MCPD_BIN_PATH_ARCH); \
		rm -f "$(MCPD_BIN_PATH)/$(MCPD_TAR)"; \
	fi
	@cp $(MCPD_BIN_PATH_ARCH) $(MCPD_BIN_PATH_BASE)


build: prepare ## Build the Docker image for the server
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

clean: stop # Remove Docker containers and images
	@rm -rf bin && echo "Successfully removed mcpd binaries"
	@docker rmi $(DOCKER_IMAGE):$(DOCKER_TAG) && echo "Successfully removed $(DOCKER_IMAGE):$(DOCKER_TAG) image"

# ====================================================================================
# Testing
# ====================================================================================

test-unit: ## Run unit tests
	@uv sync --quiet --group tests
	@pytest -v tests/unit/
	@echo "Unit tests completed successfully!"

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

test-generated-artifacts: ## Run artifact validation tests
	@if [ -z "$(PROMPT_ID)" ]; then \
		echo "Error: PROMPT_ID is required. Usage: make test-generated-artifacts PROMPT_ID=<prompt-id>"; \
		exit 1; \
	fi
	@echo "Running artifact validation tests for prompt-id: $(PROMPT_ID)..."
	@uv sync --quiet --group tests
	@pytest tests/generated_artifacts/ -m artifact_validation --prompt-id=$(PROMPT_ID) -v
	@echo "Artifact validation tests completed successfully!"

test-generated-artifacts-integration: ## Run artifact integration tests
	@if [ -z "$(PROMPT_ID)" ]; then \
		echo "Error: PROMPT_ID is required. Usage: make test-generated-artifacts-integration PROMPT_ID=<prompt-id>"; \
		exit 1; \
	fi
	@echo "Running artifact integration tests for prompt-id: $(PROMPT_ID)..."
	@uv sync --quiet --group tests
	@pytest tests/generated_artifacts/ -m artifact_integration --prompt-id=$(PROMPT_ID) -v
	@echo "Artifact integration tests completed successfully!"

# ====================================================================================
# MCP Testing and Documentation
# ====================================================================================

test-mcps: ## Run MCP server tests
	@echo "Running MCP server tests..."
	uv run python -m docs.scripts.test_mcp_servers

update-mcps: test-mcps ## Update MCP doc and registry for mcpd with the results of the tests
	@echo "Generating MCP documentation..."
	uv run python -m docs.scripts.generate_mcp_table
	@echo "Generating MCP registry..."
	uv run python -m docs.scripts.generate_mcp_registry
	@echo "MCP documentation and registry updated successfully!"

# ====================================================================================
# Documentation
# ====================================================================================

docs-build:
	@echo "Building documentation..."
	@uv sync --quiet --group docs
	@uv run mkdocs build
	@echo "Documentation built successfully!"

docs-serve-local: ## Serve documentation locally
	@echo "Starting MkDocs development server..."
	@uv sync --quiet --group docs
	@uv run mkdocs serve
