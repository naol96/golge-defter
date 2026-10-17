# Gölge Defter — ölçüm raporu

**Veritabanı:** `data/golge.db`

## Kararlar (durum)
- APPROVED_PAPER: 1
- NO_DECISION: 45
- TECHNICAL_BLOCK: 156

## Kararlar (piyasa kaynağı)
- ATK_LIVE_MARKET: 202

## Gölge defter
- Kategori: {'TECHNICAL_UNEXECUTABLE': 156}
- feed_source: {'ATK_LIVE_MARKET': 156}

## 15/60 değerlendirme
- Durum: {'COMPLETE': 147, 'PENDING': 165}
- Bekleyen: 165
- Tamamlanan 15 dk: 128 (ATK canlı: 128)
- Tamamlanan 60 dk: 19 (ATK canlı: 19)

## Engelleme sınıflandırması
- TECHNICAL_BLOCK (min emir / icra): 156
- SHADOW_RISK (Anayasa): 0

## PAPER durumu
- Bakiye: 37.48750 USDT
- Açık pozisyon: 1

## Son karar
- id=202 status=NO_DECISION symbol=ETH-USDT market_source=ATK_LIVE_MARKET

## Notlar
- PAPER only; no LIVE orders.
- FIXTURE/MOCK counts are not live market proof.
- Pending 15/60 rows are normal until horizon elapses; feed_source fills on COMPLETE.
- TECHNICAL_BLOCK/MIN_ORDER: constitutional notional (25% of balance) below adapter min order (~10 USDT), not a risk veto.
