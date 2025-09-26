FROM python:3.12-slim AS base

# Install system dependencies including GDAL
RUN apt-get update && apt-get install -y \
    curl \
    gdal-bin \
    libgdal-dev \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Set GDAL environment variables
ENV GDAL_CONFIG=/usr/bin/gdal-config
ENV CPLUS_INCLUDE_PATH=/usr/include/gdal
ENV C_INCLUDE_PATH=/usr/include/gdal

# Install UV
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Builder stage (install deps, build docs)
FROM base AS builder
COPY .  .

# Create virtual env and install deps from pyproject.toml
RUN uv venv && uv sync

# Install the local icefabric package itself in editable mode
# This registers the package in the virtual environment
RUN uv pip install -e .

# Build docs into static site
RUN uv pip install ".[docs]" && uv run mkdocs build -d /app/static/docs

# Final stage / Final Image
FROM base AS final
WORKDIR /app

# Copy virtualenv, the runnable 'app', the 'icefabric' source, and docs
COPY --from=builder /app/.venv ./.venv
COPY --from=builder /app/app ./app
COPY --from=builder /app/src ./src
COPY --from=builder /app/static/docs ./static/docs
COPY --from=builder /app/.pyiceberg.yaml .
COPY --from=builder /app/pyproject.toml .

# Set the PATH to use the virtualenv
ENV PATH="/app/.venv/bin:$PATH"

# Set the PYTHONPATH so the interpreter can find the icefabric module
ENV PYTHONPATH="/app/src"

# Create the data directory that the application needs to run
RUN mkdir /app/data

# Expose the port the application will run on
EXPOSE 8000

# Command to run the FastAPI application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]