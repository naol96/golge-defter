# Gölge Defter — ölçüm raporu

**Veritabanı:** `data/golge.db`

## Kararlar (durum)
- APPROVED_PAPER: 1
- NO_DECISION: 47
- SHADOW_RISK: 3
- TECHNICAL_BLOCK: 159

## Kararlar (piyasa kaynağı)
- ATK_LIVE_MARKET: 210

## Gölge defter
- Kategori: {'CONSTITUTIONAL_RISK_BLOCK': 3, 'TECHNICAL_UNEXECUTABLE': 159}
- feed_source: {'ATK_LIVE_MARKET': 162}

## 15/60 değerlendirme
- Durum: {'COMPLETE': 158, 'PENDING': 166}
- Bekleyen: 166
- Tamamlanan 15 dk: 131 (ATK canlı: 131)
- Tamamlanan 60 dk: 27 (ATK canlı: 27)

## Engelleme sınıflandırması
- TECHNICAL_BLOCK (min emir / icra): 159
- SHADOW_RISK (Anayasa): 3

## PAPER durumu
- Bakiye: 37.48750 USDT
- Açık pozisyon: 1

## Son karar
- id=210 status=NO_DECISION symbol=BTC-USDT market_source=ATK_LIVE_MARKET

## Notlar
- PAPER only; no LIVE orders.
- FIXTURE/MOCK counts are not live market proof.
- Pending 15/60 rows are normal until horizon elapses; feed_source fills on COMPLETE.
- TECHNICAL_BLOCK/MIN_ORDER: constitutional notional (25% of balance) below adapter min order (~10 USDT), not a risk veto.
