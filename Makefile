.PHONY: help install install-dev test test-cov lint format type-check security clean run build pre-commit

# Default target
help:
	@echo "Available targets:"

# Install project dependencies
install:
	uv sync --all-extras --all-packages


# Run tests
test:
	uv run pytest

# Run tests with coverage
test-cov:
	uv run pytest --cov=. --cov-report=term-missing --cov-report=html

# Run linting
lint:
	uv run ruff check .

# Format code
format:
	uv run ruff format .
	uv run ruff check --fix .

# Run type checking
type-check:
	uv run mypy .

# Clean up generated files
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type f -name ".coverage" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name "*.egg" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
	find . -type d -name "htmlcov" -exec rm -rf {} +
	find . -type d -name "dist" -exec rm -rf {} +
	find . -type d -name "build" -exec rm -rf {} +

# Run the game
run:
	uv run main.py

# Install pre-commit hooks
pre-commit:
	uv run pre-commit install
	uv run pre-commit run --all-files
