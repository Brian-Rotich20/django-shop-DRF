# Use official Python image
FROM python:3.11-slim

# Set environment vars
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    libffi-dev \
    default-libmysqlclient-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Install pip dependencies
COPY requirements.txt /app/
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Copy project files
COPY . /app/

# Collect static files (skip this if not needed)
RUN python manage.py collectstatic --noinput

# Expose port
EXPOSE 8000

# Start Daphne server
CMD ["gunicorn", "ecommerceApiProject.wsgi:application", "--bind", "0.0.0.0:8000"]

