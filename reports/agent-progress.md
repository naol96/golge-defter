# Agent progress

| Agent | Provider | Branch | Worktree | Durum | Not |
|-------|----------|--------|----------|--------|-----|
| shadow-ledger-supervisor | codex | main | `/home/hazar/golge-defter` | CONFIGURED | `cao profile validate` OK |
| golge-codex-core | codex | agent/codex-core | `../golge-defter-codex` | VERIFIED | core/storage/tests |
| golge-opencode-atk | opencode_cli | agent/opencode-atk | `../golge-defter-atk` | VERIFIED | OKX MCP adapter |
| golge-cursor-dashboard | cursor_cli | agent/cursor-dashboard | `../golge-defter-ui` | VERIFIED | Streamlit UI |

## CAO

- Profiller: `cao install agents/*.md` + `cao profile validate` (golge-codex-core, shadow-ledger-supervisor geçti).
- `cao launch` RUNNING oturumu bu turda başlatılmadı; sunucu: `nohup cao-server --host 127.0.0.1 --port 9889 &`.
- MVP kod entegrasyonu ana worktree'de tamamlandı (worktree'ler izolasyon için hazır).
