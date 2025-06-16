#!/usr/bin/env bash
set -e

echo ">>> Waiting for Postgres at $DB_HOST:$DB_PORT..."
until pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER"; do
  sleep 1
done
echo ">>> Postgres is up!"

echo ">>> Applying Django migrations..."
python manage.py migrate --noinput

echo ">>> Starting Daphne server..."
exec daphne -b 0.0.0.0 -p 8000 SocialProjectDemo.asgi:application
