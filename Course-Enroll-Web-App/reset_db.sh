#!/usr/bin/env bash
set -euo pipefail

# Reset and seed the local SQLite database.
ROOT="$(cd "$(dirname "$0")" && pwd)"
VENV="$ROOT/.venv"
PY=${PY:-python3}

if [ -d "$VENV" ]; then
  # Use project virtualenv when available.
  PYTHON_BIN="$VENV/bin/python"
else
  PYTHON_BIN="$PY"
fi

if [ ! -f "$ROOT/reset_and_seed_db.py" ]; then
  echo "Error: reset_and_seed_db.py not found in $ROOT"
  exit 1
fi

echo "Running database reset and seed..."
exec "$PYTHON_BIN" "$ROOT/reset_and_seed_db.py"
