# Gölge Defter — Web Kokpit

React 18 + TypeScript + Vite ile yazılmış, **salt okunur** kontrol masası. İş mantığı
yoktur: tüm kararlar Python tarafında verilir, arayüz yalnızca okur ve gösterir.

## Çalıştırma

```bash
# 1) Backend (repo kökünde)
python -m dashboard.serve_kokpit --port 8501          # API + React arayüzü (önce derleyin)

# 2a) Geliştirme: HMR, /api → 8501 proxy
cd web && npm ci && npm run dev                  # http://localhost:5173

# 2b) Üretim: derle ve Python sunucusundan servis et
cd web && npm run build
cd .. && python -m dashboard.serve_kokpit --ui web    # http://127.0.0.1:8501
```

Backend olmadan sunum için **demo modu**: `http://localhost:5173/?demo=1`
(veya bağlantı hatası bandındaki "Demo veriyle aç"). Demo verisi tarayıcıda üretilir
ve arayüzde her yerde `DEMO VERİ` olarak etiketlenir.

## Görünümler

| Kısayol | Görünüm | İçerik |
| --- | --- | --- |
| `1` | Genel bakış | KPI şeridi, zaman serisi (grafik/tablo), karar dağılımı, kural kırılımı, canlı akış, simülatör, gölge özeti |
| `2` | Karar akışı | Filtrelenebilir/aranabilir tablo, CSV, karar yolculuğu çekmecesi (veri → analist → anayasa → sonuç) |
| `3` | Gölge Defter | 15/60 dk ölçüm ilerlemesi, karşı-olgusal sonuç matrisi, gölge kayıtları |
| `4` | Anayasa | Kural kartları (canlı kullanım ölçerleri), "Anayasaya meydan oku" simülatörü, açık PAPER pozisyonlar |
| `5` | Sistem & kanıt | Worker/veri tazeliği, sinyal/veri kökenleri, yerel SHA-256 kanıtı, ölçüm notları |

Diğer kısayollar: `/` ara · `R` yenile · `P` otomatik yenilemeyi duraklat · `T` tema (sistem → açık → koyu) · `Esc` çekmeceyi kapat.

## İlkeler

- Parasal değerler API'den ondalık **string** olarak gelir; yuvarlama yalnızca görüntüde,
  BigInt ile yapılır (`src/lib/format.ts`, testli).
- Karşı-olgusal PnL hiçbir yerde "önlenen zarar" olarak sunulmaz.
- Eski `OBSERVATION`/`MIN_ORDER` risk kayıtları teknik olarak gösterilir (backend ile aynı kural).
- Renk tek başına anlam taşımaz: durumlar ikon, etiket, lejant ve tabloyla birlikte gösterilir.
- Bağlantı koparsa son iyi veri kalır ve "güncel olmayabilir" uyarısı gösterilir.

## Komutlar

```bash
npm run dev        # geliştirme sunucusu
npm run build      # tip kontrolü + üretim derlemesi (dist/)
npm run typecheck  # yalnızca tip kontrolü
npm test           # birim testleri (vitest)
```

## Bu depoya uyarlama

- Varsayılan frontend bu tasarımdır; `--ui classic` önceki HTML kokpitini açar.
- Mevcut `snapshot` ve `simulate-rule` uçları korunur. `/api/analytics` yalnızca okuma ve sunum agregasyonudur; worker veya risk motoru çalıştırmaz.
- Denetlenen `min(%5 gün başı bakiye, 5 USDT)` günlük zarar kuralı ve pariteye bağlı minimum emir açıklaması korunur.
- Anayasa paneli kod varsayılanlarıdır; karar anındaki kullanıcı sıkılaştırmaları bu özete dahil değildir.
- NO_DECISION grafikte ve sayaçlarda görünür; Gölge Defter adayı sayılmaz.
- Demo fiyatlarının kaynağı FIXTURE_SYNTHETIC_NOT_LIVE, sinyal kökeni DEMO'dur; canlı ATK gözlem sayısı sıfırdır. Demo moduna kendiliğinden geçilmez.
- PnL altı ondalık ve küçük değer göstergesiyle sunulur; hesap motorunun Decimal değerleri değiştirilmez.

Kontroller ve ekran görüntüleri: `../docs/reports/2026-10-17-faz-react-frontend-entegrasyon.md`.
