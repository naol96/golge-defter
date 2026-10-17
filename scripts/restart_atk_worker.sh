#!/usr/bin/env bash
# Controlled restart: same DB, new code (minSz, rules_v2). Run ~15:00 after backup.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
mkdir -p data logs evidence
PIDFILE="$ROOT/data/atk_worker.pid"
LOG="$ROOT/logs/atk_worker.log"
PY="$ROOT/.venv/bin/python"
STAMP="$(date +%Y%m%d_%H%M)"

cp -a data/golge.db "evidence/golge_pre_restart_${STAMP}.db"
tail -n 50 "$LOG" >"evidence/atk_worker_tail_${STAMP}.log" 2>/dev/null || true

if [[ -f "$PIDFILE" ]]; then
  old_pid="$(cat "$PIDFILE")"
  if kill -0 "$old_pid" 2>/dev/null; then
    kill "$old_pid" || true
    for _ in $(seq 1 15); do
      kill -0 "$old_pid" 2>/dev/null || break
      sleep 1
    done
  fi
fi

ANALYST="${GOLGE_ANALYST:-demo}"
USER_RULE="${GOLGE_USER_RULE:-}"
EXTRA=()
if [[ -n "$USER_RULE" ]]; then
  EXTRA+=(--user-rule "$USER_RULE")
fi

PYTHONPATH="$ROOT" nohup "$PY" "$ROOT/shadow_agent.py" \
  --source atk --analyst "$ANALYST" --db data/golge.db \
  "${EXTRA[@]}" >>"$LOG" 2>&1 &
echo $! >"$PIDFILE"
echo "Restarted ATK worker PID $(cat "$PIDFILE"). Backup: evidence/golge_pre_restart_${STAMP}.db"
