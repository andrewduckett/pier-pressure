# PierPressure task runner. Thin wrappers over uv (design D10).

# The image's Python version, which compose.yaml needs (#45).
export PYTHON_VERSION := `cat .python-version`

# Show available recipes.
default:
    @just --list

# Sync the environment, dependencies, and lockfile.
install:
    uv sync

# Lint with ruff.
lint:
    uv run ruff check .

# Format with ruff.
format:
    uv run ruff format .

# Type-check the package and scripts with mypy.
typecheck:
    uv run mypy

# Run the test suite.
test:
    uv run pytest

# Run the service.
run:
    uv run python -m pierpressure

# The full gate CI runs: lint + typecheck + test.
check: lint typecheck test

# Start a local Mosquitto broker (dev only, anonymous on 1883).
broker-up:
    docker compose up -d mosquitto

# Run PierPressure in its image against a local broker. Needs ./config.yaml.
up:
    docker compose --profile full up --build

# Stop the local dev stack.
broker-down:
    docker compose down

# Run the opt-in integration tests against a throwaway local broker: bring the
# stack up, run the tests, then tear the whole stack down (even on failure).
test-integration:
    #!/usr/bin/env bash
    set -uo pipefail
    docker compose up -d --wait mosquitto
    uv run pytest -m integration
    status=$?
    docker compose down
    exit $status
