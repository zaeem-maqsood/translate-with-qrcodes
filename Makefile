# Makefile for Translate & QR Code App

# Variables
DOCKER_COMPOSE = docker compose
CONTAINER_NAME = translate_and_qr_codes-web-1
IMAGE_NAME = translate-and-qr-codes

# Colors
GREEN = \033[0;32m
NC = \033[0m # No Color

.PHONY: help build up start stop restart logs shell clean reset-db

help:
	@echo "Usage:"
	@echo "  make build    Build the Docker image"
	@echo "  make up       Start the container in the background"
	@echo "  make start    Alias for 'make up'"
	@echo "  make stop     Stop the running container"
	@echo "  make restart  Restart the container"
	@echo "  make logs     View container logs"
	@echo "  make shell    Access the container's shell"
	@echo "  make clean    Stop and remove containers, networks, and images"
	@echo "  make reset-db Delete DB and migrations, then re-init (Dev only)"

build:
	@echo "$(GREEN)Building the Docker image...$(NC)"
	$(DOCKER_COMPOSE) build

up:
	@echo "$(GREEN)Starting the application...$(NC)"
	$(DOCKER_COMPOSE) up -d
	@echo "$(GREEN)App is running at http://localhost:8000$(NC)"

start: up

stop:
	@echo "$(GREEN)Stopping the application...$(NC)"
	$(DOCKER_COMPOSE) stop

restart: stop up

logs:
	$(DOCKER_COMPOSE) logs -f

shell:
	$(DOCKER_COMPOSE) exec web bash

clean:
	@echo "$(GREEN)Cleaning up...$(NC)"
	$(DOCKER_COMPOSE) down --rmi all --volumes --remove-orphans

reset-db:
	@echo "$(GREEN)Resetting the database...$(NC)"
	rm -f translate_and_qr_codes/db.sqlite3
	find translate_and_qr_codes/qr_codes/migrations -name "0*.py" -delete
	@echo "$(GREEN)Re-creating migrations and database...$(NC)"
	$(DOCKER_COMPOSE) run --rm web python manage.py makemigrations qr_codes
	$(DOCKER_COMPOSE) run --rm web python manage.py migrate
	@echo "$(GREEN)Database reset complete.$(NC)"
