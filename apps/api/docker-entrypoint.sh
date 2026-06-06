#!/bin/sh
set -eu

if [ "${KAIROX_RUN_MIGRATIONS:-true}" = "true" ]; then
  attempts="${KAIROX_MIGRATION_ATTEMPTS:-20}"
  sleep_seconds="${KAIROX_MIGRATION_RETRY_SECONDS:-3}"
  attempt=1

  while [ "$attempt" -le "$attempts" ]; do
    echo "Running database migrations (attempt ${attempt}/${attempts})"
    if alembic upgrade head; then
      echo "Database migrations completed"
      break
    fi

    if [ "$attempt" -eq "$attempts" ]; then
      echo "Database migrations failed after ${attempts} attempts" >&2
      exit 1
    fi

    attempt=$((attempt + 1))
    sleep "$sleep_seconds"
  done
else
  echo "Skipping database migrations because KAIROX_RUN_MIGRATIONS=false"
fi

exec "$@"
