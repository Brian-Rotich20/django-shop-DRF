# Use official Python image
FROM python:3.11-slim

# Set environment vars
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies - minimal for binary wheels
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt /app/

# Install Python dependencies using only binary wheels
RUN pip install --upgrade pip --no-cache-dir && \
    pip install --only-binary=all --no-cache-dir -r requirements.txt

# Copy project files
COPY . /app/

# Collect static files (only if needed)
RUN python manage.py collectstatic --noinput || true

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash app && \
    chown -R app:app /app
USER app

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

# Start Daphne server
CMD ["daphne", "ecommerceApiProject.asgi:application", "-b", "0.0.0.0", "-p", "8000"]