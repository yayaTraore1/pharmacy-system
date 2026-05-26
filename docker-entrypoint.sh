#!/bin/sh
set -e

echo "Starting container entrypoint"
# Debug: show whether DATABASE_URL is set (masked)
if [ -z "$DATABASE_URL" ]; then
  echo "DATABASE_URL is not set or empty"
else
  MASKED_PREFIX=$(printf '%s' "$DATABASE_URL" | cut -c1-12)
  echo "DATABASE_URL set (masked prefix): ${MASKED_PREFIX}***"
fi

if [ -f /app/alembic.ini ]; then
  echo "alembic.ini found — running migrations: alembic upgrade head"
  alembic upgrade head
else
  echo "No alembic.ini found — skipping database migrations"
fi

# Execute the container CMD
exec "$@"
