# Gölge Defter — ölçüm raporu

**Veritabanı:** `data/golge.db`

## Kararlar (durum)
- APPROVED_PAPER: 1
- NO_DECISION: 75
- SHADOW_RISK: 72
- TECHNICAL_BLOCK: 159

## Kararlar (piyasa kaynağı)
- ATK_LIVE_MARKET: 307

## Sinyal kökeni
- DEMO: 307

## Gölge defter
- Kategori: {'CONSTITUTIONAL_RISK_BLOCK': 72, 'TECHNICAL_UNEXECUTABLE': 159}
- feed_source: {'ATK_LIVE_MARKET': 231}

## 15/60 değerlendirme
- Durum: {'COMPLETE': 312, 'PENDING': 150}
- Bekleyen: 150
- Tamamlanan 15 dk: 199 (ATK canlı: 199)
- Tamamlanan 60 dk: 113 (ATK canlı: 113)

## Engelleme sınıflandırması
- TECHNICAL_BLOCK (min emir / icra): 159
- SHADOW_RISK (Anayasa): 72

## PAPER durumu
- Bakiye: 37.48750 USDT
- Açık pozisyon: 1

## Son karar
- id=307 status=SHADOW_RISK symbol=ETH-USDT market_source=ATK_LIVE_MARKET

## Notlar
- PAPER only; no LIVE orders.
- ATK market data does not imply an LLM signal; signal origins are counted separately.
- Legacy OBSERVATION/MIN_ORDER risk rows are counted as technical without rewriting stored records.
- COMPLETE counts include all categories; technical observations are not risk protection metrics.
- Live-feed counts require both entry and exit from ATK; they are not verified LLM performance.
- FIXTURE/MOCK counts are not live market proof.
- Pending 15/60 rows are normal until horizon elapses; feed_source fills on COMPLETE.
- TECHNICAL_BLOCK/MIN_ORDER: constitutional notional (25% of balance) below adapter min order (~10 USDT), not a risk veto.
