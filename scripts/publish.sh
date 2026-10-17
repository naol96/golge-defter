#!/usr/bin/env bash
# GitHub'da ilk kez PRIVATE repo oluştur ve varsayılan dalı gönder.
# Gerektirir: git + gh (https://cli.github.com/), `gh auth login`.
set -euo pipefail
cd "$(dirname "$0")/.."
if ! command -v gh >/dev/null; then
  echo "Önce GitHub CLI kur: https://cli.github.com/" >&2
  exit 1
fi
if ! gh auth status >/dev/null 2>&1; then
  echo "Önce gh auth login komutuyla GitHub'a giriş yap." >&2
  exit 1
fi
if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  git init -b main
fi
if ! git rev-parse --verify HEAD >/dev/null 2>&1; then
  git add .
  git commit -m "chore: initialize shadow ledger prototype"
fi
# Çakışmayı önlemek için kullanıcıya ait repo adını açıkça kullan.
gh repo create golge-defter --private --source=. --remote=origin --push   --description "Shadow Ledger + Investment Constitution | OKX TR Team1 Agentic Hackathon"
