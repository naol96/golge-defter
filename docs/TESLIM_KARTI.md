# Teslim Kartı (Gölge Defter)

Son güncelleme: 2026-10-17 ~14:27 TRT · Worker **dokunulmadı** · DB: `data/golge.db`

| Alan | Değer |
| --- | --- |
| Herkese açık repo | _(GitHub URL — `git push` sonrası doldurun)_ |
| Canlı kokpit | Yerel: `streamlit run dashboard/kokpit_proof.py` → http://localhost:8501 |
| Yedek video | _(17:30–18:00 çekim — Drive/YouTube liste dışı link)_ |
| ATK modu | Salt okunur MCP (`npx @okx_ai/okx-trade-mcp --modules market --read-only`) |
| ATK kanıtı (Bonus 1) | _(Order ID + saat — 15:30 kontrollü alım veya "TR demo yok" notu)_ |
| Fuji sözleşme | _(FUJI_ANCHOR_CONTRACT — Hat B)_ |
| Snowtrace tx (≥2) | _(FUJI_LAST_TX — `chain/anchor_job.py` manifest: `evidence/anchor_manifest.json`)_ |
| Gölge Defter özet | ~187 ATK karar · 1 PAPER · 15dk COMPLETE artıyor · **60dk COMPLETE başladı (≥6)** · SHADOW_RISK canlıda 0 (Hamle A: `scripts/prove_shadow_risk_atk.py` ayrı DB) |
| Analist | DEMO (LLM restart sonrası) |
| Kural sürümü (kod) | `rules_v2` · canlı worker eski MIN_ORDER süreci → **15:00 restart** planı |

## Kanıt komutları

```bash
python report.py --db data/golge.db --out evidence/measurement_report.md
python inspect_live_readonly.py --db data/golge.db
PYTHONPATH=. python scripts/prove_shadow_risk_atk.py
python chain/anchor_job.py --db data/golge.db
```

## Rehber eşlemesi

`kanit_sonrasi_eylem_ve_teslim_rehberi.md`: P0 60dk doğrulandı · Hamle A kodlandı · 17:30 freeze · 18:45 teslim.
