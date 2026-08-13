# v5.7 Maç Olay ve Senaryo Simülasyonu

## Maç olay motoru
Gol ve kırmızı kart olayları, maç öncesi expected-goals ve olay olasılıkları
üzerinden örneklenir.

## Canlı maç durumu
Simülasyon yalnızca 0-0 başlangıcından çalışmaz. Dakika, skor ve kırmızı kart
durumu verilerek maçın kalan bölümü simüle edilebilir.

## Monte Carlo raporu
Binlerce tekrar sonunda:
- ev galibiyeti,
- beraberlik,
- deplasman galibiyeti,
- ortalama goller,
- kırmızı kart oranları,
- en sık skor
raporlanır.

## Senaryo karşılaştırması
Baz senaryo ile örneğin 70. dakikada 0-1 geride olunan durum arasındaki olasılık
değişimi hesaplanır.

## Üretim sınırı
Bu sürüm olay bağımsızlığı ve sade Poisson varsayımları kullanır. Gerçek maç
temposu, oyuncu değişiklikleri, zamanla değişen hazard rate ve tracking data
henüz modele bağlı değildir.
