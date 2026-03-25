#!/usr/bin/env bash
set -euo pipefail

# Simple runner for development: creates venv, installs deps, and starts server
ROOT="$(cd "$(dirname "$0")" && pwd)"
VENV="$ROOT/.venv"
PY=${PY:-python3}

if [ ! -d "$VENV" ]; then
  echo "Creating virtualenv at $VENV"
  "$PY" -m venv "$VENV"
fi

echo "Activating virtualenv"
. "$VENV/bin/activate"

echo "Installing dependencies"
pip install --upgrade pip
pip install -r "$ROOT/requirements.txt"

# Free port 8000 if needed
PID=$(lsof -t -iTCP:8000 -sTCP:LISTEN || true)
if [ -n "$PID" ]; then
  echo "Killing process on :8000 (PID $PID)"
  kill -9 $PID || true
fi

echo "Starting server on http://127.0.0.1:8000"
exec uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
