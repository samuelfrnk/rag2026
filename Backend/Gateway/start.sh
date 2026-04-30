#!/usr/bin/env bash
# Start the FastAPI gateway.
#
# Local dev:
#   ./start.sh
#
# On Nuvolos (port 8000 proxied at /proxy/8000/):
#   ROOT_PATH=/proxy/8000 ./start.sh
#
# Or set the env var before running:
#   export ROOT_PATH=/proxy/8000
#   ./start.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

: "${PORT:=8000}"
: "${HOST:=0.0.0.0}"
: "${ROOT_PATH:=}"          # e.g. /proxy/8000 on Nuvolos

echo "Starting arXiv RAG Gateway on ${HOST}:${PORT} (root_path='${ROOT_PATH}')"

# Activate venv if present
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
fi

ROOT_PATH="$ROOT_PATH" uvicorn main:app \
    --host "$HOST" \
    --port "$PORT" \
    --root-path "$ROOT_PATH"
