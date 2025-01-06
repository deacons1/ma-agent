FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy the application into the container
COPY . /app

# Install the application dependencies
WORKDIR /app
RUN uv sync --frozen --no-cache

# Create and set permissions for gunicorn temp directory
RUN mkdir -p /dev/shm/gunicorn && chmod 777 /dev/shm/gunicorn

# Run the application with gunicorn
CMD ["/app/.venv/bin/gunicorn", "src.api.main:app", "-c", "gunicorn_config.py", "--worker-tmp-dir", "/dev/shm/gunicorn"] 