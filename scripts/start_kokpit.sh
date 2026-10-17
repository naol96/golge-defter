#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

PY="${ROOT}/.venv/bin/python"
if [[ ! -x "$PY" ]]; then
  PY=python3
fi

mkdir -p logs data
PIDFILE="data/kokpit.pid"

if [[ -f "$PIDFILE" ]]; then
  old_pid="$(cat "$PIDFILE")"
  if kill -0 "$old_pid" 2>/dev/null; then
    echo "Stopping kokpit pid=$old_pid"
    kill "$old_pid" 2>/dev/null || true
    sleep 1
  fi
fi

nohup "$PY" -m dashboard.serve_kokpit --host 127.0.0.1 --port 8501 \
  >> logs/kokpit.log 2>&1 &
echo $! > "$PIDFILE"
echo "Kokpit http://127.0.0.1:8501 (pid $(cat "$PIDFILE"))"
echo "Legacy Streamlit: streamlit run dashboard/kokpit_proof.py"
