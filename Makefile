# Makefile for Pyfecto project
# Helps with building, testing, and publishing

.PHONY: clean install test lint format build publish tag-release help

# Virtual environment directory
VENV = .venv
POETRY_VERSION := $(shell poetry version -s)
EPOCH := $(shell date +%s)

# Set an epoch version for the main branch
CURRENT_BRANCH := $(shell git rev-parse --abbrev-ref HEAD)
ifeq ($(CURRENT_BRANCH), main)
    VERSION := 0.0.$(EPOCH)
else
    VERSION := $(POETRY_VERSION)
endif

TAG := v$(VERSION)

help:
	@echo "Pyfecto Project Makefile"
	@echo "------------------------"
	@echo "clean      	- Remove build artifacts and cached files"
	@echo "install    	- Install dependencies and the package in development mode"
	@echo "test       	- Run tests"
	@echo "lint       	- Run linting checks"
	@echo "format     	- Format code using black, isort"
	@echo "build      	- Build the package distribution"
	@echo "publish    	- Publish the package to PyPI"
	@echo "version    	- Display the current package version"
	@echo "tag-release	- Bump version and create git tag."

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
	@poetry install
	@echo "Installation complete!"

test:
	@echo "Running tests..."
	@poetry run pytest -v tests/
	@echo "Tests complete!"

test-cov:
	@echo "Running tests with coverage..."
	@poetry run pytest --cov=src/pyfecto tests/
	@echo "Coverage tests complete!"

lint:
	@echo "Running linters..."
	@poetry run flake8 src/pyfecto tests
	@poetry run mypy src/pyfecto
	@echo "Linting complete!"

format:
	@echo "Formatting code..."
	@poetry run black src/pyfecto tests
	@poetry run isort src/pyfecto tests
	@echo "Formatting complete!"

build:
	@echo "Building package..."
	@poetry build
	@echo "Build complete!"

publish:
	@echo "Publishing to PyPI..."
	@poetry publish
	@echo "Publish complete!"

publish-test:
	@echo "Publishing to Test PyPI..."
	@poetry publish -r testpypi
	@echo "Test publish complete!"

version:
	@echo "Current package version:"
	@echo "${VERSION}"

tag-release:
	@echo "Tagging release..."
	@git tag -a ${TAG} -m "release tag" && git push origin ${TAG}
	@echo "✅ Release ${TAG} completed!"