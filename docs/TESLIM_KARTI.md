# Teslim Kartı (Gölge Defter)

Son güncelleme: 2026-10-17 ~15:10 TRT · Worker **rules_v2** aktif · DB: `data/golge.db` (salt okunur kokpit)

| Alan | Değer |
| --- | --- |
| Repo | https://github.com/hazarkasap/golge-defter (private) · yerelde **push bekliyor** |
| Canlı kokpit | `bash scripts/start_kokpit.sh` → http://127.0.0.1:8501 (koyu web UI; yedek Streamlit) |
| Yedek video | _(siz çekin — 75–90 sn; link buraya)_ |
| ATK modu | Salt okunur MCP (`npx @okx_ai/okx-trade-mcp --modules market --read-only`) |
| ATK kanıtı (Bonus 1) | **307** karar `ATK_LIVE_MARKET`; spot emir: _(yoksa "TR demo yok" + SS)_ |
| Fuji | `evidence/anchor_manifest.json` — `LOCAL_SHA256`, **blockchain_verified=false** |
| Snowtrace tx (≥2) | **Eksik** (`FUJI_ANCHOR_CONTRACT` + test AVAX) |
| Gölge Defter özet | **307** karar · **1** PAPER · **199×** 15dk · **113×** 60dk · **72** SHADOW_RISK · **159** TECHNICAL_BLOCK |
| Analist (canlı) | **DEMO** (tüm canlı `signal_origin`) |
| Analist (LLM) | Mock: `evidence/llm_single_cycle.txt` (OpenRouter `.env`) |
| Kural sürümü | **`rules_v2`** · LLM worker: `GOLGE_ANALYST=llm bash scripts/restart_atk_worker.sh` |

## Kanıt komutları

```bash
python report.py --db data/golge.db --out evidence/measurement_report.md
python inspect_live_readonly.py --db data/golge.db
PYTHONPATH=. python scripts/prove_shadow_risk_atk.py
python chain/anchor_job.py --db data/golge.db
```

## Rehber eşlemesi

`kanit_sonrasi_eylem_ve_teslim_rehberi.md`: P0 60dk doğrulandı · Hamle A kodlandı · 17:30 freeze · 18:45 teslim.
