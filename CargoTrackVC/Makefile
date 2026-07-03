.PHONY: help install test test-cov test-integration lint format docker-build docker-up docker-down docker-test clean

help:
	@echo "CargoTrack VC - Available commands:"
	@echo "  make install      - Install dependencies"
	@echo "  make test         - Run tests"
	@echo "  make test-cov     - Run tests with coverage"
	@echo "  make test-integration - Run integration tests"
	@echo "  make lint         - Run linters"
	@echo "  make format       - Format code"
	@echo "  make docker-build - Build Docker images"
	@echo "  make docker-up    - Start Docker services"
	@echo "  make docker-down  - Stop Docker services"
	@echo "  make docker-test  - Run tests in Docker"
	@echo "  make clean        - Clean build artifacts"

install:
	pip install -e ".[dev]"

test:
	pytest tests/unit -v

test-cov:
	pytest tests/ -v --cov=dte_mvp --cov-report=term-missing --cov-report=html

test-integration:
	pytest tests/integration -v

lint:
	ruff check src/ tests/
	mypy src/

format:
	ruff check --fix src/ tests/
	ruff format src/ tests/

docker-build:
	docker compose -f docker/docker-compose.yml build

docker-up:
	docker compose -f docker/docker-compose.yml up -d

docker-down:
	docker compose -f docker/docker-compose.yml down

docker-test:
	docker compose -f docker/docker-compose.test.yml up --build

clean:
	rm -rf build/ dist/ *.egg-info/ .pytest_cache/ .coverage htmlcov/ .mypy_cache/ .ruff_cache/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
