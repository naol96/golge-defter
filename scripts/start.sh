#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
MODE=${1:-cli}
if [[ "$MODE" == "dashboard" ]]; then
  PYTHONPATH=. .venv/bin/streamlit run dashboard/app.py
else
  PYTHONPATH=. .venv/bin/python main.py --source atk "$@"
fi
