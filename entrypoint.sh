#!/bin/sh
set -e #exit the script if anything fails

echo "Running collectstatic..."
python3 manage.py collectstatic --no-input

echo "Running migrations..."
python3 manage.py migrate --no-input

echo "Starting Gunicorn..."
exec gunicorn track_locator.wsgi:application \
  --bind 0.0.0.0:8000 \
  --workers 3 \
  --threads 2 \
  --timeout 120 \
  --max-requests 1000 \
  --max-requests-jitter 100 \
  --log-level info \
  --access-logfile - \
  --error-logfile -

