#!/usr/bin/env bash
set -e

# 1) Wait for Postgres to be ready
echo ">>> Waiting for Postgres at $DB_HOST:$DB_PORT..."
until pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER"; do
  sleep 1
done
echo ">>> Postgres is up!"

# 2) Apply Django migrations
echo ">>> Applying Django migrations..."
python manage.py migrate --noinput

# 3) Start Daphne (ASGI server for Channels)
echo ">>> Starting Daphne server..."
exec daphne -b 0.0.0.0 -p 8000 SocialProjectDemo.asgi:application
