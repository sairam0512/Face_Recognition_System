import os

# Read PORT from cloud environment (Railway / Render / Heroku) or default to 5000
port = os.environ.get("PORT", "5000")
bind = f"0.0.0.0:{port}"

workers = 2
threads = 2
timeout = 120
keepalive = 5
