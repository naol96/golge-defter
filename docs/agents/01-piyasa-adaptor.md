# Rol: Piyasa veri adaptörü

OKX Agent Trade Kit (ATK) üzerinden **salt okunur** fiyat; çıktı `MarketSnapshot`.

## Kapsam (minimal)

- Yeni modül önerisi: `src/golge_defter/market.py` (tek dosya, ~100 satır üst sınır hedefi)
- Girdi: izinli parite (`AVAX-USDT`, `BTC-USDT`, `ETH-USDT`)
- Çıktı: `MarketSnapshot(pair, bid, ask, captured_at)` — `risk.py` ile uyumlu
- Timeout: **3 sn**; bayat eşik: `Constitution.max_data_age_seconds` (10 sn)

## Davranış

| Durum | Sonuç |
| --- | --- |
| ATK yanıt vermez | `None` veya açık hata; **sabit fiyat kullanma** |
| Bid/ask tutarsız | `evaluate` zaten `NO_DECISION` döner; adaptör mümkünse erken filtrele |
| Ağ kapalı (test) | `pytest` içinde **inject edilen** fake snapshot; gerçek HTTP testleri `@pytest.mark.network` ile ayrı |

## Yapma

- Emir, bakiye veya API trade scope
- Çoklu exchange soyutlama katmanı
- Retry storm (en fazla 1–2 deneme)

## Test (paralel hazırla)

- `tests/test_market.py`: mock HTTP/ATK yanıtı → snapshot parse
- Mevcut `tests/test_risk.py` **değişmeden** geçmeli
- Komut: `pytest -q -n auto tests/test_market.py tests/test_risk.py`

## Faz raporu bölümü

- ATK bağımlılığı nasıl kuruldu (env, opsiyonel extra)
- Hangi pariteler doğrulandı
- Örnek snapshot (MOCK etiketli)

## Referans

- [OKX Agent Trade Kit](https://github.com/okx/agent-trade-kit)
- `docs/architecture.md` katman 1
