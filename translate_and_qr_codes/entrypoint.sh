#!/bin/sh

# Exit immediately if a command exits with a non-zero status
set -e

# Run database migrations
echo "Running database migrations..."
python manage.py migrate

# Start the application
echo "Starting application..."
exec gunicorn translate_and_qr_codes.wsgi:application --bind 0.0.0.0:8000
