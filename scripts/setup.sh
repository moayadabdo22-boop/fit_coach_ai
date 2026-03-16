#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

ensure_env_file() {
  local target="$1"
  local example="$2"
  if [[ ! -f "$target" && -f "$example" ]]; then
    cp "$example" "$target"
  fi
}

echo "Setting up FitCoach AI..."

# Create env files if missing
ensure_env_file ".env" ".env.example"
ensure_env_file "ai_backend/.env" "ai_backend/.env.example"

if [[ "${SKIP_BACKEND:-}" != "1" ]]; then
  if command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="python3"
  elif command -v python >/dev/null 2>&1; then
    PYTHON_BIN="python"
  else
    echo "Python is not installed or not on PATH."
    exit 1
  fi

  if [[ ! -d "ai_backend/venv" ]]; then
    "$PYTHON_BIN" -m venv "ai_backend/venv"
  fi

  # shellcheck disable=SC1091
  source "ai_backend/venv/bin/activate"
  pip install --upgrade pip
  pip install -r "ai_backend/requirements.txt"
  deactivate
fi

if [[ "${SKIP_FRONTEND:-}" != "1" ]]; then
  if ! command -v npm >/dev/null 2>&1; then
    echo "npm is not installed or not on PATH."
    exit 1
  fi
  npm install
fi

echo "Done."
echo "Run backend: ./ai_backend/venv/bin/python -m uvicorn app:app --host 127.0.0.1 --port 8000"
echo "Run frontend: npm run dev"
