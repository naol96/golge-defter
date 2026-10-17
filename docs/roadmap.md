# Hackathon yapılacaklar

## Hazır (başlangıç reposu)

- [x] Proje tanıtımı, güvenlik sınırları ve mimari belgeleri
- [x] `BUY` / `PASS` risk kararı ve deterministik boyutlama
- [x] Kuralları gevşetmeyen pozisyon tavanı değişimi ve açık uyarı
- [x] Bayat veri, günlük zarar, minimum emir ve spread reddi
- [x] En az 6 güvenlik senaryosu için testler
- [x] CI test iş akışı

## Sonraki aşamalar — henüz uygulanmadı

- [ ] OKX ATK ile doğrulanmış salt-okunur market veri adaptörü
- [ ] Nitel sinyal üreten AI ajan adaptörü (tutar/emir yetkisi yok)
- [ ] SQLite `executed_trades` ve `shadow_trades` kayıtları
- [ ] Gölge kayıt için 15 ve 60 dakika idempotent gözlem takipçisi
- [ ] Net ücret hesaplama; intra-bar stop kontrolü / sınırlama etiketi
- [ ] PAPER açık pozisyon takipçisi ve zarar kesme işlemi
- [ ] Streamlit karar kartları ve otomatik yenilenen kokpit
- [ ] Kill-switch, API kapsam kontrolü ve *ayrı* LIVE güvenlik incelemesi
- [ ] Demo kayıtları ve hackathon sunumu

> `scripts/publish.sh` GitHub CLI bulunan ve yetkili oturum açmış bir makinede yeni PRIVATE repo oluşturur. Bu ortamdan uzaktaki GitHub reposu henüz oluşturulmuş değildir.
