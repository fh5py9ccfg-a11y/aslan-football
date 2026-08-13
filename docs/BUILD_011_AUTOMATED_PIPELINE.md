# Build 011 — Automated Prediction Pipeline

## Otomatik çalışma

- Yaklaşan fikstürleri bulur
- Otomatik oyuncu eksikliği etkisini hesaplar
- Toplu tahmin üretir
- Güven ve veri kalitesi uyarıları oluşturur
- Teknik ekip onay akışını kaydeder
- Tek sayfalık karar raporu üretir

## İnsan kontrolü

Tahmin karar durumları:

- PENDING
- APPROVED
- REJECTED
- NEEDS_REVIEW

Model çıktısı teknik ekibin karar desteğidir; insan onayı olmadan kesin karar
olarak değerlendirilmemelidir.
