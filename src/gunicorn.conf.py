# gunicorn.conf.py

import multiprocessing
import os

# Server socket
bind = '0.0.0.0:8000'  # Bind to all available addresses on port 8000

# Worker processes
workers = multiprocessing.cpu_count() + 1  # Number of worker processes

# Worker class
worker_class = 'sync'  # The type of workers to use (default: 'sync')

# Logging
accesslog = '-'  # Log access data to stdout
errorlog = '-'  # Log errors to stdout
loglevel = 'info'  # Logging level

# Timeouts
timeout = 30  # Workers silent for more than this many seconds are killed and restarted
graceful_timeout = 30  # Timeout for graceful workers restart

# Security
# For an extra layer of security, you might want to set a custom umask, like '0077'
# This will restrict read/write permissions to the owner only
# umask = 0o0077

# Gunicorn internal settings
# These are advanced settings that can help with debugging or optimization
# Keep-alive requests are served from the same worker, reducing the overhead of establishing a new connection
keepalive = 2  # Seconds to wait for requests on a Keep-Alive connection
preload_app = True  # Load application code before the worker processes are forked

# Worker tmp settings
# Ensures that Gunicorn creates temporary files in the container's memory
worker_tmp_dir = '/dev/shm'

# Metrics
# Add the following to expose Prometheus metrics, assuming you've integrated the prometheus_client in your app
metrics_port = 8001

