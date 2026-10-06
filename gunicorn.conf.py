import sys
import os

# Intercept sys.argv before Gunicorn parses CLI flags to replace literal '$PORT' with actual numeric port
port = os.environ.get("PORT", "5000")

for i, arg in enumerate(sys.argv):
    if "$PORT" in arg:
        sys.argv[i] = arg.replace("$PORT", port)

# Set bind address to 0.0.0.0:<PORT>
bind = f"0.0.0.0:{port}"
workers = 2
threads = 2
timeout = 120
keepalive = 5
