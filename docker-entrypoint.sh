#!/bin/bash
set -e

echo "Waiting for PostgreSQL [$POSTGRES_HOST] to be ready..."
until PGPASSWORD=$POSTGRES_PASSWORD psql -h "$POSTGRES_HOST" -U "$POSTGRES_USER" -d "auto_artel" -c '\q' 2>/dev/null; do
  >&2 echo "PostgreSQL is unavailable - sleeping"
  sleep 2
done

echo "PostgreSQL is up - continuing..."

echo "Running database migrations..."
python manage.py migrate --noinput

echo "Starting Daphne server..."
exec daphne -b 0.0.0.0 -p 8888 auto_artel.asgi:application