FROM python:3.11-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy the application into the container
COPY . /app

# Install the application dependencies
WORKDIR /app
RUN uv sync --frozen --no-cache

# Run the application with gunicorn
CMD ["/app/.venv/bin/gunicorn", "src.api.main:app", "-c", "gunicorn_config.py"] 