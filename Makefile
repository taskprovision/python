# =============================================================================
# Project Configuration
# =============================================================================
PROJECT_NAME := taskprovision
PACKAGE_NAME := taskprovision
PYTHON := python3
POETRY := $(shell command -v poetry 2> /dev/null || echo "poetry")

# =============================================================================
# Directory Structure
# =============================================================================
SRC_DIR := src/$(PROJECT_NAME)
TEST_DIR := tests
CORE_DIR := $(SRC_DIR)/core
DOCS_DIR := docs
BUILD_DIR := build
DIST_DIR := dist
VENV_DIR := .venv

# =============================================================================
# Development Settings
# =============================================================================
DEV_PORT := 8000
DOCS_PORT := 8001
COVERAGE_REPORT := htmlcov
DOCKER_COMPOSE := docker-compose

# =============================================================================
# File Patterns
# =============================================================================
PYTHON_SRC := $(shell find $(SRC_DIR) -type f -name '*.py')
PYTHON_TESTS := $(shell find $(TEST_DIR) -type f -name '*.py')

# =============================================================================
# Output Formatting
# =============================================================================
GREEN  := $(shell tput -Txterm setaf 2)
YELLOW := $(shell tput -Txterm setaf 3)
WHITE  := $(shell tput -Txterm setaf 7)
RESET  := $(shell tput -Txterm sgr0)
TICK   := $(GREEN)✓$(RESET)

# =============================================================================
# Helper Functions
# =============================================================================
define log_info
	@echo "$(YELLOW)»$(RESET) $(1)"
endef

define log_success
	@echo "$(TICK) $(GREEN)$(1)$(RESET)"
endef

# =============================================================================
# Main Targets
# =============================================================================
.DEFAULT_GOAL := help

# Get the list of targets from the Makefile
HELP_TARGETS := $(shell grep -E '^[a-zA-Z0-9_-]+:.*?## .*$$' $(MAKEFILE) | \
	sort | \
	awk 'BEGIN {FS = ":.*?## "}; \
		 {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}')

.PHONY: help
##@ Help
help:  ## Display this help
	@echo "$(YELLOW)$(PROJECT_NAME) - Makefile$(RESET)"
	@echo "\n$(WHITE)Usage: make $(GREEN)<target>$(RESET)"
	@echo "\n$(YELLOW)Available targets:$(RESET)"
	@echo "$(HELP_TARGETS)"

##@ Setup
.PHONY: install install-dev install-hooks check-env

install: check-env  ## Install package in development mode with all dependencies
	$(call log_info,Installing package in development mode...)
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -U poetry
	$(POETRY) install --with dev --extras "cli server"
	$(call log_success,Package installed in development mode)

install-dev:  ## Install development dependencies
	$(call log_info,Installing development dependencies...)
	$(POETRY) install --with dev
	$(call log_success,Development dependencies installed)

install-hooks:  ## Install git hooks
	$(call log_info,Installing pre-commit hooks...)
	$(POETRY) run pre-commit install
	$(call log_success,Pre-commit hooks installed)

check-env:  ## Check environment configuration
	$(call log_info,Checking environment configuration...)
	@if [ ! -f .env ]; then \
		echo "$(YELLOW)⚠️  .env file not found. Creating from example...$(RESET)"; \
		cp -n .env.example .env 2>/dev/null || true; \
	fi
	$(call log_success,Environment configuration checked)

##@ Development
.PHONY: start start-dev start-ollama start-prod start-docker

start: start-dev  ## Alias for start-dev

start-dev: check-env  ## Start development server
	$(call log_info,Starting development server...)
	@$(POETRY) run uvicorn $(PROJECT_NAME).api:app --reload --port $(DEV_PORT)

start-ollama:  ## Start Ollama server
	$(call log_info,Starting Ollama server...)
	@echo "$(YELLOW)ℹ️  Keep this running in a separate terminal$(RESET)"
	ollama serve

start-prod: check-env  ## Start production server
	$(call log_info,Starting production server on port $(PROD_PORT)...)
	@$(POETRY) run uvicorn $(PROJECT_NAME).api:app --host 0.0.0.0 --port $(PROD_PORT)

start-docker:  ## Start using Docker
	$(call log_info,Starting with Docker...)
	@$(DOCKER_COMPOSE) up --build

##@ Testing & Quality
.PHONY: test test-cov lint format check

test:  ## Run tests
	$(call log_info,Running tests...)
	$(POETRY) run pytest $(TEST_DIR) -v

test-cov:  ## Run tests with coverage
	$(call log_info,Running tests with coverage...)
	$(POETRY) run pytest --cov=$(SRC_DIR) --cov-report=term-missing --cov-report=html $(TEST_DIR) -v

lint:  ## Run all linters
	$(call log_info,Running linters...)
	$(POETRY) run black --check $(SRC_DIR) $(TEST_DIR)
	$(POETRY) run flake8 $(SRC_DIR) $(TEST_DIR)
	$(POETRY) run mypy $(SRC_DIR) $(TEST_DIR)

format:  ## Format code
	$(call log_info,Formatting code...)
	$(POETRY) run black $(SRC_DIR) $(TEST_DIR)
	$(POETRY) run isort $(SRC_DIR) $(TEST_DIR)

check: lint test  ## Run all checks (lint and test)

##@ Build & Publish
.PHONY: build publish

build:  ## Build package
	$(call log_info,Building package...)
	$(POETRY) version patch
	$(POETRY) build
	$(call log_success,Package built in $(DIST_DIR)/)

publish: build  ## Publish package to PyPI
	$(call log_info,Publishing to PyPI...)
	$(POETRY) publish

##@ Documentation
.PHONY: docs serve-docs

docs:  ## Generate documentation
	$(call log_info,Generating documentation...)
	@$(POETRY) run mkdocs build

serve-docs:  ## Serve documentation locally
	$(call log_info,Serving documentation at http://localhost:$(DOCS_PORT))
	@$(POETRY) run mkdocs serve -a 127.0.0.1:$(DOCS_PORT)

##@ Cleanup
.PHONY: clean clean-all clean-docker clean-node

clean:  ## Remove build and test artifacts
	$(call log_info,Cleaning up...)
	@# Python artifacts
	@find . -type f -name '*.py[co]' -delete -o \
		-type d -name '__pycache__' -exec rm -rf {} + -o \
		-type f -name '*~' -delete
	@find . -type d -name '.pytest_cache' -exec rm -rf {} + || true
	@rm -f .coverage coverage.xml
	@rm -rf $(COVERAGE_REPORT) $(BUILD_DIR) $(DIST_DIR) *.egg-info
	$(call log_success,Clean complete)

clean-all: clean  ## Remove all artifacts including virtualenvs
	$(call log_info,Removing virtual environments...)
	@rm -rf $(VENV_DIR) .venv/
	$(call log_success,All clean!)

clean-docker:  ## Stop and remove Docker containers and volumes
	$(call log_info,Cleaning Docker resources...)
	@if command -v $(DOCKER_COMPOSE) >/dev/null 2>&1; then \
		$(DOCKER_COMPOSE) down -v --remove-orphans || true; \
	else \
		echo "$(YELLOW)⚠️  Docker Compose not found, skipping...$(RESET)"; \
	fi

clean-node:  ## Remove node_modules (kept for backward compatibility)
	@# This target is kept for compatibility but may be removed in future
	$(call log_info,Cleaning Node.js modules...)
	@rm -rf node_modules package-lock.json 2>/dev/null || true

# =============================================================================
# Utility Targets
# =============================================================================
.PHONY: run-example update-docs docker-up docker-down

run-example:  ## Run the example script
	$(call log_info,Running example...)
	$(POETRY) run python -m $(PROJECT_NAME).taskprovision

update-docs: docs  ## Alias for docs
	$(call log_success,Documentation updated)

docker-up:  ## Start Docker containers
	$(call log_info,Starting Docker containers...)
	@$(DOCKER_COMPOSE) up -d

docker-down:  ## Stop Docker containers
	$(call log_info,Stopping Docker containers...)
	@$(DOCKER_COMPOSE) down

docker-logs:  ## Show Docker logs
	@echo "$(YELLOW)Showing Docker logs...$(NC)"
	@$(DOCKER_COMPOSE) logs -f

##@ Cleanup
clean:  ## Clean build artifacts
	$(call log_info,Cleaning build artifacts...)
	@rm -rf build/ dist/ *.egg-info/ htmlcov/ .coverage .pytest_cache/
	@find . -name '*.pyc' -delete
	@find . -name '__pycache__' -delete

clean-docs:  ## Clean documentation build
	$(call log_info,Cleaning documentation...)
	@rm -rf site/ docs/build/

clean-all: clean clean-docs  ## Clean everything (including Docker)
	$(call log_info,Cleaning everything including Docker...)
	@rm -rf .mypy_cache/ .pytest_cache/ .coverage htmlcov/
	@find . -name '*.pyc' -delete -o -name '__pycache__' -delete -o -name '.pytest_cache' -delete
	@if command -v $(DOCKER_COMPOSE) >/dev/null 2>&1; then \
		$(DOCKER_COMPOSE) down -v --remove-orphans || true; \
	else \
		echo "$(YELLOW)⚠️  Docker Compose not found, skipping...$(RESET)"; \
	fi
	$(call log_success,All clean!)

##@ Help
help:  ## Show this help message
	@awk 'BEGIN {FS = ":.*##"; printf "\n$(YELLOW)Usage:$(NC)\n  make \033[36m<target>\033[0m\n"} /^[a-zA-Z_-]+:.*?##/ { printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2 } /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

##@ Documentation
docs:  ## Generate API documentation
	$(call log_info,Generating documentation...)
	@mkdir -p docs/source
	$(POETRY) run sphinx-apidoc -o docs/source $(PACKAGE_NAME)
	$(POETRY) run sphinx-build -b html docs/source docs/build
	$(call log_success,Docs built at docs/build/index.html)

##@ Project Management
portfolio:  ## Generate project portfolio
	$(call log_info,Generating portfolio...)
	$(POETRY) run python -m $(PACKAGE_NAME).cli generate-portfolio

##@ Git
git-init:  ## Initialize git repository
	$(call log_info,Initializing git repository...)
	git init
	git add .
	git commit -m "Initial commit"
	$(call log_success,Git repository initialized)

##@ Phony Targets
.PHONY: help setup-env install install-dev test test-cov lint format docs serve-docs \
        build publish docker-up docker-down docker-logs clean clean-all help \
        portfolio git-init

