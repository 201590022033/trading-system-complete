#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON="${PYTHON:-${PROJECT_ROOT}/.venv/bin/python}"
PORT="${PORT:-5000}"
HOST="${HOST:-0.0.0.0}"

if [[ ! -x "${PYTHON}" ]]; then
    echo "Missing Python environment: ${PYTHON}" >&2
    echo "Create it with: python3 -m venv .venv && .venv/bin/python -m pip install -r requirements.txt" >&2
    exit 1
fi

if ! "${PYTHON}" -c 'import flask, flask_socketio' >/dev/null 2>&1; then
    echo "Dashboard dependencies are missing from ${PYTHON}" >&2
    echo "Install them with: ${PYTHON} -m pip install -r requirements.txt" >&2
    exit 1
fi

cd "${PROJECT_ROOT}"
echo "Starting dashboard from ${PROJECT_ROOT}/app.py on ${HOST}:${PORT}"
echo "Open the forwarded port in your workspace; health check: http://127.0.0.1:${PORT}/health"
exec env HOST="${HOST}" PORT="${PORT}" "${PYTHON}" app.py
