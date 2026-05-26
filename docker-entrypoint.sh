#!/bin/sh
set -e

echo "Starting container entrypoint"

if [ -f /app/alembic.ini ]; then
  echo "alembic.ini found — running migrations: alembic upgrade head"
  alembic upgrade head
else
  echo "No alembic.ini found — skipping database migrations"
fi

# Execute the container CMD
exec "$@"
