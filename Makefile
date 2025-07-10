.PHONY: dev all docker-prune docker-purge

dev:
	docker compose -f docker-compose.yaml -f docker-compose.dev.yaml up --watch --build

all:
	docker compose -f docker-compose.yaml up --build

docker-prune:
	@echo "Removing all unused docker containers, networks, and images..."
	docker system prune -a -f

docker-purge:
	@echo "WARNING: This will remove all your docker images and volumes."
	docker system prune -a --volumes -f
