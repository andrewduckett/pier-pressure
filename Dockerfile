# uv-based build (design D10): install deps in a builder, then a slim runtime
# layer that runs the module. This is a plain container, not a HAOS add-on.
FROM python:3.12-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never

# Install dependencies first (cached unless the lockfile changes), without the
# project or dev tooling, then install the project itself.
COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --no-install-project --no-dev

COPY pierpressure ./pierpressure
RUN uv sync --frozen --no-dev


FROM python:3.12-slim

WORKDIR /app
COPY --from=builder /app /app
ENV PATH="/app/.venv/bin:$PATH"

# Config is provided at runtime, e.g. `-v ./config.yaml:/app/config.yaml` plus
# `-e PIERPRESSURE_MQTT_PASSWORD=...`.
ENTRYPOINT ["python", "-m", "pierpressure"]
