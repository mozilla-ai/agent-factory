# Makefile for Agent Factory

# Configuration
DOCKER_IMAGE = agent-factory
DOCKER_CONTAINER = agent-factory-a2a
DOCKER_TAG = latest
A2A_SERVER_HOST = localhost
A2A_SERVER_PORT = 8080

# Default target
.PHONY: help
help:
	@echo "Available targets:"
	@echo "  build           - Build the Docker image for Agent Factory A2A server"
	@echo "  run             - Run the A2A server in Docker"
	@echo "  stop            - Stop the running container"
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
		-p $(A2A_SERVER_PORT):8080 \
		--env-file .env \
		$(DOCKER_IMAGE):$(DOCKER_TAG)
	@echo "Server running at http://$(A2A_SERVER_HOST):$(A2A_SERVER_PORT)"

# Stop the running container
.PHONY: stop
stop:
	@docker stop $(DOCKER_CONTAINER) 2>/dev/null || true

# Clean up Docker resources
.PHONY: clean
clean: stop
	@docker rmi $(DOCKER_IMAGE):$(DOCKER_TAG) 2>/dev/null || true

# Default target
.DEFAULT_GOAL := help
