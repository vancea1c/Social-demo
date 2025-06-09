# Use an official lightweight Python image
FROM python:3.11-slim

# Don’t write .pyc files and don’t buffer stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system-level dependencies, including libpq-dev for psycopg2
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    postgresql-client \
    curl \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Set working directory inside container
WORKDIR /code

# Copy and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy your entire project into the container
COPY . .

# (Optional) Copy and make entrypoint.sh executable
COPY entrypoint.sh /code/entrypoint.sh
RUN chmod +x /code/entrypoint.sh

# Expose port 8000 (Django’s default)
EXPOSE 8000

# Docker health check: poll /health/ every 30s
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost:8000/health/ || exit 1

# Use entrypoint.sh so that we wait for DB, run migrations, and then start Daphne
ENTRYPOINT ["/code/entrypoint.sh"]
