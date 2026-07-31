# Use Python 3.12-slim as the builder stage
FROM python:3.12-slim AS builder

# Install uv for extremely fast and reliable dependency installation
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set working directory to match the final runtime path
WORKDIR /home/user/app

# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies (running as root so cache mount permissions work perfectly)
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev

# Final runtime stage
FROM python:3.12-slim

# Force Python stdout and stderr streams to be unbuffered to enable real-time logs in Docker/Render
ENV PYTHONUNBUFFERED=1

# Create a non-root user (UID 1000) for security compatibility
RUN useradd -m -u 1000 user
USER user
WORKDIR /home/user/app

# Copy the virtual environment from builder and change ownership to the non-root user
COPY --from=builder --chown=user:user /home/user/app/.venv /home/user/app/.venv

# Copy application source files with correct owner permissions
COPY --chown=user:user src/ /home/user/app/src/

# Place the virtual environment's bin folder at the front of the PATH
ENV PATH="/home/user/app/.venv/bin:$PATH"

# Configure PYTHONPATH so python can resolve 'src' correctly
ENV PYTHONPATH="/home/user/app"

# Default fallback port (Render injects a $PORT environment variable)
EXPOSE 10000

# Start FastAPI by calling python -m uvicorn directly from the virtual environment path
CMD ["sh", "-c", "/home/user/app/.venv/bin/python -m uvicorn src.main:app --host 0.0.0.0 --port ${PORT:-10000}"]
