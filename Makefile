# Makefile for Agent Factory

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
	@echo "  build           - Build the Docker image for Agent Factory A2A server"
	@echo "  run             - Run the A2A server in Docker"
	@echo "  stop            - Stop the running agent-factory-a2a container"
	@echo "  clean           - Remove Docker containers and images"

# Build the Docker image
.PHONY: build
build:
	docker build --build-arg APP_VERSION=$(shell git describe --tags --dirty 2>/dev/null || echo "dev") -t $(DOCKER_IMAGE):$(DOCKER_TAG) .

# Run the server in Docker
.PHONY: run
run: build
	@if [ ! -f .env ]; then \
		echo "Error: .env file not found. Please create one with your API keys."; \
		exit 1; \
	fi
	docker run --rm -d \
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
	@docker stop $(DOCKER_CONTAINER)
	@echo "Successfully stopped $(DOCKER_CONTAINER) container"

.PHONY: clean
clean: stop
	@docker rmi $(DOCKER_IMAGE):$(DOCKER_TAG)
	@echo "Successfully removed $(DOCKER_IMAGE):$(DOCKER_TAG) image"

# Default target
.DEFAULT_GOAL := help
