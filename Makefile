# Makefile for Pyfecto project
# Helps with building, testing, and publishing

.PHONY: clean install test lint format build publish help

# Virtual environment directory
VENV = .venv
# Python interpreter
PYTHON = python3
# Poetry executable
POETRY = poetry

help:
	@echo "Pyfecto Project Makefile"
	@echo "------------------------"
	@echo "clean      - Remove build artifacts and cached files"
	@echo "install    - Install dependencies and the package in development mode"
	@echo "test       - Run tests"
	@echo "lint       - Run linting checks"
	@echo "format     - Format code using black, isort"
	@echo "build      - Build the package distribution"
	@echo "publish    - Publish the package to PyPI"
	@echo "version    - Display the current package version"

clean:
	@echo "Cleaning up..."
	@rm -rf build/
	@rm -rf dist/
	@rm -rf *.egg-info
	@find . -type d -name __pycache__ -exec rm -rf {} +
	@find . -type f -name "*.pyc" -delete
	@find . -type f -name "*.pyo" -delete
	@find . -type f -name "*.pyd" -delete
	@find . -type f -name ".coverage" -delete
	@find . -type d -name "*.egg" -exec rm -rf {} +
	@find . -type d -name ".pytest_cache" -exec rm -rf {} +
	@find . -type d -name ".coverage" -exec rm -rf {} +
	@echo "Clean complete!"

install:
	@echo "Installing dependencies and package in dev mode..."
	@$(POETRY) install
	@echo "Installation complete!"

test:
	@echo "Running tests..."
	@$(POETRY) run pytest -v tests/
	@echo "Tests complete!"

test-cov:
	@echo "Running tests with coverage..."
	@$(POETRY) run pytest --cov=src/pyfecto tests/
	@echo "Coverage tests complete!"

lint:
	@echo "Running linters..."
	@$(POETRY) run flake8 src/pyfecto tests
	@$(POETRY) run mypy src/pyfecto
	@echo "Linting complete!"

format:
	@echo "Formatting code..."
	@$(POETRY) run black src/pyfecto tests
	@$(POETRY) run isort src/pyfecto tests
	@echo "Formatting complete!"

build:
	@echo "Building package..."
	@$(POETRY) build
	@echo "Build complete!"

publish:
	@echo "Publishing to PyPI..."
	@$(POETRY) publish
	@echo "Publish complete!"

publish-test:
	@echo "Publishing to Test PyPI..."
	@$(POETRY) publish -r testpypi
	@echo "Test publish complete!"

version:
	@echo "Current package version:"
	@$(POETRY) version -s