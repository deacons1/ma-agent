import multiprocessing
import os

# Get the PORT from environment variable
port = os.getenv("PORT", "8000")

# Gunicorn config variables
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "uvicorn.workers.UvicornWorker"
bind = f"0.0.0.0:{port}"
keepalive = 120
timeout = 120
graceful_timeout = 120
max_requests = 1000
max_requests_jitter = 50

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"

# Worker temporary directory
worker_tmp_dir = "/dev/shm/gunicorn" 