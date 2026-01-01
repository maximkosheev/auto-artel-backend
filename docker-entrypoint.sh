#!/bin/bash
set -e

echo "Waiting for PostgreSQL [$DB_HOST] to be ready..."
until PGPASSWORD=$DB_PASSWORD psql -h "$DB_HOST" -U "$DB_USER" -d "auto_artel" -c '\q' 2>/dev/null; do
  >&2 echo "PostgreSQL is unavailable - sleeping"
  sleep 2
done

echo "PostgreSQL is up - continuing..."

echo "Running database migrations..."
python manage.py migrate --noinput

echo "Creating groups, users, permissions"
python manage.py init

echo "Creating superuser"
python manage.py createadmin --username "admin" --email "admin@email.com" --noinput

echo "Starting Daphne server..."
exec daphne -b 0.0.0.0 -p 8888 auto_artel.asgi:application