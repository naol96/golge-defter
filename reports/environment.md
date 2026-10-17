# Ortam raporu — 2026-10-17

## Sistem

| Alan | Değer |
|------|--------|
| OS | Linux (CachyOS), x86_64 |
| Çalışma dizini | `/home/hazar/golge-defter` |
| Disk (/) | ~149G boş |
| RAM | 15 GiB |

## Araç sürümleri

| Araç | Sürüm | Durum |
|------|--------|--------|
| Python | 3.14.7 (.venv) | OK |
| Node.js | v24.22.0 | OK |
| npm | 11.19.1 | OK |
| uv | 0.12.10 | OK |
| tmux | 3.7c | OK |
| Git | main (origin ahead) | OK |
| CAO (`cao`) | 2.5.4 | OK |
| `cao-server` | kurulu | Manuel başlatma gerekli |
| Codex CLI | 0.163.0 | OK |
| OpenCode CLI | v2.0.32 | OK |
| Cursor CLI | 2026.10.16 | OK |

## OKX ATK

- Paket: `@okx_ai/okx-trade-mcp` (npx)
- Modül: `market` (`--read-only`)
- Doğrulama: `market_get_ticker` AVAX-USDT → `source=ATK` ile `main.py` PASS

## Notlar

- `cao-server` bu oturumda otomatik doğrulanmadı (port 9889 yanıt vermedi); `nohup cao-server &` ile başlatılabilir.
- MVP varsayılanı: **PAPER only**, LIVE reddedilir.
