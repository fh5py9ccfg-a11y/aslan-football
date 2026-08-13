# Build 005 — Match Intelligence & Score Prediction

## Model

İlk model Poisson skor dağılımını şu sinyallerle birleştirir:

- Hücum gücü
- Savunma gücü
- Son form
- İç saha ve deplasman performansı
- Ev sahibi avantajı
- Oyuncu eksikliği etkisi
- Rakip oyuncu eksikliği etkisi

## Çıktılar

- Beklenen gol
- 1X2 olasılıkları
- Tahmini skor
- En olası beş skor
- Güven seviyesi
- Açıklama faktörleri
- Tahmin riskleri
- Tahmin geçmişi
- Sonuç ve tam skor doğruluğu
- Ortalama gol hatası

## Sınır

Bu sistem karar desteğidir. Futboldaki rastlantısallık, kadro değişiklikleri,
taktik tercihler, kırmızı kartlar ve maç içi olaylar nedeniyle kesin sonuç
garantisi vermez. Güvenilirlik gerçek geçmiş veri miktarı ve kalitesiyle artar.
