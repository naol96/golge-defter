#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
PYTHONPATH=. .venv/bin/pytest -q -n auto "$@"
