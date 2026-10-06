# uv-based build (design D10): install deps in a builder, then a slim runtime
# layer that runs the module. This is a plain container, not a HAOS add-on.

# The Python version comes from .python-version, its only pin (#45). The build has
# no default, so a build that does not pass it fails at the first FROM. CI and the
# release workflow read .python-version; the Justfile and the Nix dev shell export it
# for Compose.
ARG PYTHON_VERSION

# Pinned to match [tool.uv] required-version in pyproject.toml (design D5). A named
# stage, not `COPY --from=<image>`, because Dependabot reads only FROM lines (#26).
FROM ghcr.io/astral-sh/uv:0.12.23 AS uv

FROM python:${PYTHON_VERSION}-slim AS builder

COPY --from=uv /uv /usr/local/bin/uv

WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never

# Install dependencies first (cached unless the lockfile changes), without the
# project or dev tooling, then install the project itself.
COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --no-install-project --no-dev

# The build has no git history, so the release workflow passes the version in
# (design D1). Declared after the dependency layer, so a new version rebuilds only
# the project. Without it, the package reports its non-release fallback version.
ARG PIERPRESSURE_VERSION=""
COPY pierpressure ./pierpressure
RUN SETUPTOOLS_SCM_PRETEND_VERSION="$PIERPRESSURE_VERSION" uv sync --frozen --no-dev


FROM python:${PYTHON_VERSION}-slim

WORKDIR /app
COPY --from=builder /app /app
ENV PATH="/app/.venv/bin:$PATH"

# Config is provided at runtime, e.g. `-v ./config.yaml:/app/config.yaml` plus
# `-e PIERPRESSURE_MQTT_PASSWORD=...`.
ENTRYPOINT ["python", "-m", "pierpressure"]
