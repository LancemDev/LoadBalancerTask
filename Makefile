.PHONY: build up down restart logs clean test

# Default variables
SERVICE ?= all

# Build all or specific service
build:
	docker-compose build $(SERVICE)

# Start all services in detached mode
up:
	docker-compose up -d

# Stop and remove all containers
down:
	docker-compose down

# Restart all or specific service
restart:
	docker-compose restart $(SERVICE)

# Show logs for all or specific service
logs:
	docker-compose logs -f $(SERVICE)

# Clean up all containers, networks, and volumes
clean:
	docker-compose down -v
	docker system prune -f

# Run tests
test:
	echo "Running tests..."
	# Add your test commands here

# Show help
help:
	@echo "Available commands:"
	@echo "  make build [SERVICE=service]   - Build all or specific service"
	@echo "  make up                       - Start all services"
	@echo "  make down                     - Stop and remove all containers"
	@echo "  make restart [SERVICE=service]- Restart all or specific service"
	@echo "  make logs [SERVICE=service]   - Show logs for all or specific service"
	@echo "  make clean                    - Clean up all containers, networks, and volumes"
	@echo "  make test                     - Run tests"
	@echo "  make help                     - Show this help"

# Set default target
.DEFAULT_GOAL := help
