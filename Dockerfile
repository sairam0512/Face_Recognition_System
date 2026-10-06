# Use official lightweight Python image
FROM python:3.11-slim

# Prevent Python from buffering stdout/stderr and writing .pyc files
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system packages required by OpenCV and dlib (C++ compilers, CMake, OpenGL, GLib)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Upgrade pip and pin setuptools to prevent pkg_resources removal warnings
RUN pip install --no-cache-dir --upgrade pip "setuptools<82" wheel

# Copy requirements
COPY requirements.txt .

# Install dependencies (installing dlib natively for Linux container)
RUN pip install --no-cache-dir dlib face_recognition gunicorn Flask Werkzeug Jinja2 Pillow numpy opencv-python

# Patch gunicorn entry point so any CLI argument containing $PORT is automatically sanitized before validation
RUN python -c 'import gunicorn.app.wsgiapp as w; path = w.__file__; open(path, "w").write("import sys, os\nport = os.environ.get(\"PORT\", \"5000\")\nsys.argv = [a.replace(\"\$PORT\", port) for a in sys.argv]\n" + open(path).read())'

# Copy application source code
COPY . .

# Expose port 5000 (Railway assigns $PORT automatically)
EXPOSE 5000

# Start application server using gunicorn
CMD ["gunicorn", "app:app"]
