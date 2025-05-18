#!/bin/sh

echo "Running collectstatic..."
python3 manage.py collectstatic --no-input

echo "Running migrations..."
python3 manage.py makemigrations --no-input
python3 manage.py migrate --no-input

echo "Starting Gunicorn..."
exec gunicorn track_locator.wsgi:application --bind 0.0.0.0:8000
