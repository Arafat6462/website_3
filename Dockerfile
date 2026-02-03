# =============================================================================
# Dockerfile - E-Commerce Backend Development Image
# =============================================================================
# Purpose: Creates a Python 3.12 development environment for Django
# Usage: Used by docker-compose.dev.yml for local development
# =============================================================================

FROM python:3.12-slim

# -----------------------------------------------------------------------------
# Environment Configuration
# -----------------------------------------------------------------------------
# PYTHONDONTWRITEBYTECODE: Prevents Python from writing .pyc files
# PYTHONUNBUFFERED: Ensures Python output is sent straight to terminal
# -----------------------------------------------------------------------------
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# -----------------------------------------------------------------------------
# System Dependencies
# -----------------------------------------------------------------------------
# Install required system packages for PostgreSQL and image processing
# -----------------------------------------------------------------------------
RUN apt-get update && apt-get install -y --no-install-recommends \
    # PostgreSQL client libraries (required for psycopg)
    libpq-dev \
    # Build tools for compiling Python packages
    gcc \
    # For healthcheck
    curl \
    # Clean up apt cache to reduce image size
    && rm -rf /var/lib/apt/lists/*

# -----------------------------------------------------------------------------
# Working Directory
# -----------------------------------------------------------------------------
WORKDIR /app

# -----------------------------------------------------------------------------
# Python Dependencies
# -----------------------------------------------------------------------------
# Copy requirements first to leverage Docker layer caching
# This means dependencies are only reinstalled when requirements change
# -----------------------------------------------------------------------------
COPY requirements/ /app/requirements/

# Install Python dependencies
# --no-cache-dir: Don't cache pip packages (smaller image)
# --upgrade: Ensure pip itself is up to date
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements/dev.txt

# -----------------------------------------------------------------------------
# Application Code
# -----------------------------------------------------------------------------
# Copy the entire project (in dev, this is overridden by volume mount)
# -----------------------------------------------------------------------------
COPY . /app/

# -----------------------------------------------------------------------------
# Set Working Directory to Source
# -----------------------------------------------------------------------------
# Django manage.py is located in src/ directory
# -----------------------------------------------------------------------------
WORKDIR /app/src

# -----------------------------------------------------------------------------
# Port Exposure
# -----------------------------------------------------------------------------
# Django development server runs on port 8000
# -----------------------------------------------------------------------------
EXPOSE 8000

# -----------------------------------------------------------------------------
# Default Command
# -----------------------------------------------------------------------------
# Start Django development server
# 0.0.0.0: Listen on all interfaces (required for Docker)
# -----------------------------------------------------------------------------
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
