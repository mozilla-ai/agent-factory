# Makefile for Agent Factory

# mcpd
MCPD_VERSION ?= $(shell curl -s https://api.github.com/repos/mozilla-ai/mcpd/releases/latest | jq -r .tag_name)
MCPD_ARCH ?= $(shell uname -m | sed 's/x86_64/x86_64/; s/arm64/arm64/')
MCPD_TAR = mcpd_Linux_$(MCPD_ARCH).tar.gz
MCPD_URL = https://github.com/mozilla-ai/mcpd/releases/download/$(MCPD_VERSION)/$(MCPD_TAR)
MCPD_BIN_PATH = bin
MCPD_BASE_NAME = mcpd
MCPD_BIN_PATH_BASE=$(MCPD_BIN_PATH)/$(MCPD_BASE_NAME)
MCPD_BIN_PATH_ARCH=$(MCPD_BIN_PATH)/$(MCPD_BASE_NAME)_$(MCPD_ARCH)

# Configuration
DOCKER_IMAGE = agent-factory
DOCKER_CONTAINER = agent-factory-a2a
DOCKER_TAG = latest
A2A_SERVER_HOST = localhost
A2A_SERVER_LOCAL_PORT = 8080

# Default environment variables
FRAMEWORK?=openai
MODEL?=o3
HOST?=0.0.0.0
PORT?=8080
LOG_LEVEL?=info
CHAT?=1

# Default target
.PHONY: help
help:
	@echo "Available targets:"
	@echo "  prepare         - Prepare required binaries via download"
	@echo "  build           - Build the Docker image for Agent Factory A2A server"
	@echo "  run             - Run the A2A server in Docker"
	@echo "  stop            - Stop the running agent-factory-a2a container"
	@echo "  clean           - Remove Docker containers, images and any downloaded binaries"

# Prepare mcpd binary for Docker container
.PHONY: prepare
prepare:
	@mkdir -p bin
	@if [ ! -f $(MCPD_BIN_PATH_ARCH) ]; then \
		echo "Downloading mcpd binary for $(MCPD_ARCH)..."; \
		curl -sSL $(MCPD_URL) -o $(MCPD_TAR); \
		tar -xzf $(MCPD_TAR); \
		mv mcpd $(MCPD_BIN_PATH_ARCH); \
		chmod +x $(MCPD_BIN_PATH_ARCH); \
		rm -f $(MCPD_TAR); \
	fi
	@cp $(MCPD_BIN_PATH_ARCH) $(MCPD_BIN_PATH_BASE)

# Build the Docker image
.PHONY: build
build: prepare
	docker build --build-arg APP_VERSION=$(shell git describe --tags --dirty 2>/dev/null || echo "dev") -t $(DOCKER_IMAGE):$(DOCKER_TAG) .

# Run the server in Docker
.PHONY: run
run: build
	@if [ ! -f .env ]; then \
		echo "Error: .env file not found. Please create one with your API keys."; \
		exit 1; \
	fi
	docker run --rm \
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
	@echo "Server running at http://$(A2A_SERVER_HOST):$(A2A_SERVER_LOCAL_PORT)"

.PHONY: stop
stop:
	@if [ "$$(docker ps -q -f name=$(DOCKER_CONTAINER))" ]; then \
        docker stop $(DOCKER_CONTAINER) && \
        echo "Successfully stopped $(DOCKER_CONTAINER) container"; \
    else \
        echo "No $(DOCKER_CONTAINER) container running"; \
    fi

# Remove Docker containers and images
.PHONY: clean
clean: stop
	@rm -rf bin && echo "Successfully removed mcpd binaries"
	@docker rmi $(DOCKER_IMAGE):$(DOCKER_TAG) && echo "Successfully removed $(DOCKER_IMAGE):$(DOCKER_TAG) image"

# Default target
.DEFAULT_GOAL := help
