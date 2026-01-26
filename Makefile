.PHONY: help install dev db-start db-stop migrate makemigrations run shell test lint format

help:
	@echo "Commandes disponibles:"
	@echo "  make install      - Installe les dépendances"
	@echo "  make dev          - Lance l'environnement de dev complet"
	@echo "  make db-start     - Démarre PostgreSQL et Redis (Docker)"
	@echo "  make db-stop      - Arrête les services Docker"
	@echo "  make migrate      - Applique les migrations"
	@echo "  make makemigrations - Crée les migrations"
	@echo "  make run          - Lance le serveur de développement"
	@echo "  make shell        - Lance le shell Django"
	@echo "  make test         - Lance les tests"
	@echo "  make lint         - Vérifie le code (ruff)"
	@echo "  make format       - Formate le code (black, isort)"

install:
	pip install -e ".[dev]"

dev: db-start migrate run

db-start:
	docker-compose up -d
	@echo "Attente du démarrage de PostgreSQL..."
	@sleep 3

db-stop:
	docker-compose down

migrate:
	python manage.py migrate

makemigrations:
	python manage.py makemigrations

run:
	python manage.py runserver

shell:
	python manage.py shell

createsuperuser:
	python manage.py createsuperuser

test:
	pytest

lint:
	ruff check .

format:
	black .
	isort .
	ruff check --fix .

collectstatic:
	python manage.py collectstatic --noinput
