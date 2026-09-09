#!/usr/bin/env bash
set -euo pipefail

if [[ -z "${DATABASE_URL:-}" ]]; then
    echo "DATABASE_URL is required for Railway startup" >&2
    exit 1
fi
if [[ "${DATABASE_URL}" != postgres://* && "${DATABASE_URL}" != postgresql://* ]]; then
    echo "DATABASE_URL must be a PostgreSQL URL" >&2
    exit 1
fi
export APP_MODE="${APP_MODE:-RESEARCH}"
exec gunicorn --bind "0.0.0.0:${PORT:-8080}" --workers 1 app:app
