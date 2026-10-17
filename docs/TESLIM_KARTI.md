# Teslim Kartı (Gölge Defter)

Son güncelleme: 2026-10-17 ~14:35 TRT · Worker **rules_v2 restart yapıldı** · DB: `data/golge.db`

| Alan | Değer |
| --- | --- |
| Repo | https://github.com/hazarkasap/golge-defter (private; jüriye invite) |
| Canlı kokpit | `bash scripts/start_kokpit.sh` → http://127.0.0.1:8501 (yedek: `streamlit run dashboard/kokpit_proof.py`) |
| Yedek video | _(17:30–18:00 çekim — link buraya)_ |
| ATK modu | Salt okunur MCP (`npx @okx_ai/okx-trade-mcp --modules market --read-only`) |
| ATK kanıtı (Bonus 1) | Read-only MCP + canlı `ATK_LIVE_MARKET` kararları; spot emir: _(15:30 veya "TR demo yok")_ |
| Fuji sözleşme | Yerel manifest hazır; on-chain: `FUJI_ANCHOR_CONTRACT` + cüzdan gerekli |
| Snowtrace tx (≥2) | _(henüz yok — `evidence/anchor_manifest.json` sha256 kanıtı var)_ |
| Gölge Defter özet | **208+** ATK karar · **1** PAPER · **128×** 15dk · **19×** 60dk COMPLETE · **canlı SHADOW_RISK** (Kural 2 `EXPOSURE`, `rules_v2`) + Hamle A SPREAD ayrı DB |
| Analist | DEMO (canlı worker) |
| Kural sürümü | Canlı worker **`rules_v2`** (`decisions.rules_version`); restart: `bash scripts/restart_atk_worker.sh` |

## Kanıt komutları

```bash
python report.py --db data/golge.db --out evidence/measurement_report.md
python inspect_live_readonly.py --db data/golge.db
PYTHONPATH=. python scripts/prove_shadow_risk_atk.py
python chain/anchor_job.py --db data/golge.db
```

## Rehber eşlemesi

`kanit_sonrasi_eylem_ve_teslim_rehberi.md`: P0 60dk doğrulandı · Hamle A kodlandı · 17:30 freeze · 18:45 teslim.
