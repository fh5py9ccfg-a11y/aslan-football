# Build 014 — Walk-Forward Validation & Leakage Guard

## Walk-forward test

Her hedef maç için yalnızca o maçtan önceki tamamlanmış maçlar kullanılır.
Gelecek maçların sonuçlarının modele sızması engellenir.

Ölçümler:

- Sonuç doğruluğu
- Tam skor doğruluğu
- Ortalama gol hatası
- Brier skoru
- Leakage kontrol durumu

## Otomatik rakip profili

Rakiple geçmiş karşılaşmalar yalnızca belirtilen cutoff tarihinden önceyse
kullanılır.

## Reproducibility

Tahmin input ve output fingerprint'leri SHA-256 ile kaydedilir. Aynı girdilerin
aynı çıktıyı üretip üretmediği izlenebilir.
