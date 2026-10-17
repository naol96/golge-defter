# İlerleme ve kanıt raporu — 17 Ekim 2026

- **Tarih:** 2026-10-17 (TRT, ~13:55)
- **Kapsam:** PAPER/MOCK, LIVE emir yok
- **Git:** `main` (origin'den 7 commit önde)
- **Son commit:** `b886527` (OKX minSz + rapor zenginleştirme)

## Özet (tek paragraf)

Gölge Defter hackathon MVP'si: OKX ATK **salt okunur** piyasa verisi (`npx @okx_ai/okx-trade-mcp --modules market --read-only`), arka plan **ATK worker**, SQLite **karar defteri** (`decisions`), **PAPER** simülasyonu, **Gölge Defter** (15/60 dk) ve **kanıt raporu** (`report.py`) üretim hattı çalışır durumda. Canlı kanıt: **97** ATK kaynaklı karar, **1** onaylı PAPER pozisyon, **42** tamamlanmış **15 dk** değerlendirme (`feed_source=ATK_LIVE_MARKET`). **60 dk** tamamlanmış ölçüm henüz **0** (ilk vadeler ~14:24 TRT civarı). Çoğu karar **TECHNICAL_BLOCK / MIN_ORDER** (anayasal %25 tavan < eski 10 USDT sabiti); **SHADOW_RISK / anayasa veto** kaydı yok.

## Zaman çizelgesi (bugün)

| Saat (yaklaşık) | Olay |
| --- | --- |
| Sabah | Faz 0: agent dokümantasyonu, mimari, `risk.py` prototip |
| Öğle | Hackathon MVP: adaptör, pipeline, dashboard iskeleti |
| 13:19+ | **PLAN_1840**: `start_atk.sh`, `shadow_agent.py`, `decisions` tablosu, worker log/PID |
| 13:27+ | `report.py --out`, `golge.db` yolu netleştirme |
| 13:34+ | İlk **APPROVED_PAPER** (AVAX); ardından MIN_ORDER dalgası |
| 13:38+ | İlk **15 dk COMPLETE** gölge değerlendirmeleri (canlı feed) |
| 13:44+ | Kullanıcı kanıt dosyaları (`evidence/`) |
| 13:45+ | P0 doğrulama: evaluator çalışıyor; kodda OKX `minSz` (worker restart bekliyor) |
| 13:50+ | `docs/yatirim_anayasasi.md` eklendi (inceleme: MVP/kod hizası kısmi) |

## Teslim edilen bileşenler

### P0 — Canlı veri ve otonom döngü

| Bileşen | Dosya / komut | Durum |
| --- | --- | --- |
| OKX ATK MCP adaptör | `adapters/okx_atk.py` | Çalışıyor (`ATK_LIVE_MARKET`) |
| Arka plan worker | `shadow_agent.py`, `start_atk.sh` | Aktif (`data/atk_worker.pid`, `logs/atk_worker.log`) |
| Tek döngü CLI | `main.py --source atk` | Doğrulandı (bid/ask, veri yaşı) |
| Karar kaydı | `decisions` + gölge tabloları | 97 canlı karar |
| Salt okuma denetim | `inspect_live_readonly.py` | Worker'a dokunmuyor |

### PAPER ve Anayasa motoru

| Özellik | Durum |
| --- | --- |
| %25 tavan, 3 parite, spread, stop | Uygulanıyor (`core/constitution.py`, `decision_engine`) |
| PAPER pozisyon | 1 açık; bakiye ~37,49 USDT |
| MIN_ORDER / TECHNICAL_UNEXECUTABLE | 82 kayıt (teknik, risk değil) |
| Günlük zarar limiti | Kod: **5 USDT** (doküman: %5 ≈ 2,5 USDT — hizalanmalı) |
| Kural 2 (max 2 pozisyon), Kural 7 (15 dk bekleme), 40 USDT gözlem | Dokümanda var, kodda **henüz yok** |

### Gölge Defter (15/60 dk)

| Metrik | Değer |
| --- | --- |
| Gölge kayıtları | 82 (`TECHNICAL_UNEXECUTABLE`) |
| Değerlendirme COMPLETE | 42 |
| Değerlendirme PENDING | 122 |
| 15 dk canlı (`complete_15m_live_feed`) | **42** |
| 60 dk canlı (`complete_60m_live_feed`) | **0** (beklenen, vade dolmadı) |
| `decisions_shadow_risk` | **0** |

### Kanıt ve raporlama

- `report.py`: JSON/Markdown özet, teknik vs risk ayrımı, `--out` desteği
- `evidence/measurement_report.md`, `evidence/report_20261017_1344.md`
- `PLAN_1840.md`: 18:40 sprint tablosu

### Analist

- Demo analist: worker varsayılanı (`signal_origin=DEMO`)
- LLM analist: entegrasyon + **fail-closed** PASS (`--analyst llm`); başarılı canlı LLM BUY kanıtı henüz zorunlu değil

### Test ve CI

- Test paketi: `tests/` (risk, shadow, min_order, report, integration, …)
- Oturumda `python -m pytest` global ortamda modül yok; geliştirme ortamında **19 test PASS** bildirildi (commit `f65225c` sonrası)
- CI: `.github/workflows/tests.yml`

### Dokümantasyon

- `AGENTS.md`, `docs/agents/*` rolleri
- `docs/architecture.md`, `docs/roadmap.md`
- `docs/reports/2026-10-17-faz-0-agent-dokumantasyonu.md`
- **`docs/yatirim_anayasasi.md`** (kullanıcı eklentisi; git'te henüz commit edilmemiş olabilir)

### Henüz minimal / bekleyen

- **Streamlit kokpit** (`dashboard/app.py` iskelet; 4 panel jüri planı uygulanmadı)
- Worker'ın yeni **OKX minSz** kodu (commit `b886527`) canlı döngüde **aktif değil** (restart yapılmadı — bilinçli)
- İlk **60 dk** canlı çift (jüri asgari kriteri): ~14:24 TRT sonrası kontrol

## Commit özeti (main, son 7)

```text
b886527 Use OKX minSz for min order notional and enrich evidence report.
37a94f5 Clarify MIN_ORDER diagnostics and show open PAPER positions.
b0e99f6 fix(report): add --out markdown and clarify golge.db path
f65225c PLAN_1840 P0: ATK worker, decisions ledger, evidence report.
2b31396 Hackathon MVP: OKX ATK adapter, core pipeline, dashboard, CAO agents.
a17c39c Paralel test dokümantasyonu ile pyproject uyumu.
fd6c12c Agent rolleri ve faz rapor rehberi eklendi.
```

## Jüri kabul kriterleri — durum

| Kriter | Durum |
| --- | --- |
| Otonom karar | Evet (worker döngüsü) |
| OKX ATK gerçek bid/ask | Evet |
| Anayasa gerekçeli engel/onay | Evet (MIN_ORDER teknik olarak ayrı etiketli) |
| PAPER, LIVE yok | Evet |
| Tamamlanmış 15/60 canlı çift | **15 dk evet**; **60 dk bekliyor** |
| Teknik / PASS / risk / demo ayrımı | Rapor + inspect ile kısmen; kokpit eksik |
| Tekrarlanabilirlik | Git + SQLite + testler |

## Bilinçli kısıtlar ve riskler

1. **MIN_ORDER yoğunluğu:** İlk PAPER sonrası %25 tavan 10 USDT altına düşüyor; jüriye "anayasa risk veto" olarak yanlış okunabilir — doküman ve inspect metni bunu düzeltiyor.
2. **Canlı worker eski min emir kuralı:** Yeniden başlatma kanıt DB'sini karıştırmamak için ertelendi.
3. **Anayasa dokümanı vs kod:** 7 maddenin bir kısmı henüz motorde; sunumda "MVP tablosu" şart.
4. **LLM:** Fail-closed kanıtı var; üretken model sinyali canlıda doğrulanmadı.

## Sonraki adımlar (PLAN_1840 ile uyumlu)

1. **~14:24 TRT:** `python report.py --db data/golge.db --out evidence/measurement_report.md` → `complete_60m_live_feed >= 1`
2. Anayasa hizası (günlük limit, Kural 2/7 veya MVP etiketi) — **ayrı test DB**
3. Minimal Streamlit kokpit (4 panel, salt okunur `golge.db`)
4. Sunum README, ekran görüntüleri, 2,5 dk demo akışı
5. Teslim öncesi: pytest + demo; worker restart kararı ayrı

## Komutlar (kanıt yenileme)

```bash
cd ~/golge-defter
python inspect_live_readonly.py --db data/golge.db
python report.py --db data/golge.db --out evidence/measurement_report.md
tail -n 20 logs/atk_worker.log
```

---

*Bu rapor worker ve `data/golge.db` dosyasına yazma yapılmadan, salt okunur ölçümlerle üretilmiştir.*
