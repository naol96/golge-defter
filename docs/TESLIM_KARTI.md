# Teslim Kartı (Gölge Defter)

Son güncelleme: 2026-10-17 ~14:33 TRT · Worker **aktif (restart öncesi)** · DB: `data/golge.db`

| Alan | Değer |
| --- | --- |
| Repo | https://github.com/hazarkasap/golge-defter (private; jüriye invite) |
| Canlı kokpit | `streamlit run dashboard/kokpit_proof.py` → http://localhost:8501 |
| Yedek video | _(17:30–18:00 çekim — link buraya)_ |
| ATK modu | Salt okunur MCP (`npx @okx_ai/okx-trade-mcp --modules market --read-only`) |
| ATK kanıtı (Bonus 1) | Read-only MCP + canlı `ATK_LIVE_MARKET` kararları; spot emir: _(15:30 veya "TR demo yok")_ |
| Fuji sözleşme | Yerel manifest hazır; on-chain: `FUJI_ANCHOR_CONTRACT` + cüzdan gerekli |
| Snowtrace tx (≥2) | _(henüz yok — `evidence/anchor_manifest.json` sha256 kanıtı var)_ |
| Gölge Defter özet | **202** ATK karar · **1** PAPER · **128×** 15dk · **19×** 60dk COMPLETE (`ATK_LIVE_MARKET`) · gölge id **1–3** 15+60 çifti · SHADOW_RISK canlı **0** (MIN_ORDER); anayasa veto: `evidence/shadow_risk_atk.db` + `evidence/shadow_risk_proof.json` |
| Analist | DEMO (canlı worker) |
| Kural sürümü | Kod `rules_v2`; canlı süreç restart öncesi eski MIN_ORDER → **`bash scripts/restart_atk_worker.sh` ~15:00** |

## Kanıt komutları

```bash
python report.py --db data/golge.db --out evidence/measurement_report.md
python inspect_live_readonly.py --db data/golge.db
PYTHONPATH=. python scripts/prove_shadow_risk_atk.py
python chain/anchor_job.py --db data/golge.db
```

## Rehber eşlemesi

`kanit_sonrasi_eylem_ve_teslim_rehberi.md`: P0 60dk doğrulandı · Hamle A kodlandı · 17:30 freeze · 18:45 teslim.
