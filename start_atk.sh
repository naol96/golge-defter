#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"
mkdir -p data logs
PIDFILE="$ROOT/data/atk_worker.pid"
LOG="$ROOT/logs/atk_worker.log"
PY="$ROOT/.venv/bin/python"
if [[ ! -x "$PY" ]]; then
  echo "Missing venv at $ROOT/.venv — run: python -m venv .venv && pip install -e '.[dev]'" >&2
  exit 1
fi
if [[ -f "$PIDFILE" ]]; then
  old_pid="$(cat "$PIDFILE")"
  if kill -0 "$old_pid" 2>/dev/null; then
    echo "ATK worker already running (PID $old_pid). Log: $LOG"
    exit 0
  fi
fi
PYTHONPATH="$ROOT" nohup "$PY" "$ROOT/shadow_agent.py" --source atk --analyst demo \
  >>"$LOG" 2>&1 &
echo $! >"$PIDFILE"
echo "Started ATK worker PID $(cat "$PIDFILE"). Log: $LOG"
