# Gunicorn configuration

# Bind to all interfaces on port 8080
bind = "0.0.0.0:8080"

# Number of worker processes
workers = 2  # Adjust based on your server's CPU cores

# Threads per worker
threads = 4  # Increase for I/O-bound tasks

# Timeout in seconds before workers are killed
timeout = 120

# Log level
loglevel = "info"

# Access log file
accesslog = "-"

# Error log file
errorlog = "-"
