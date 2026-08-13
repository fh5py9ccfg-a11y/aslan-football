# Build 013 — Post-Match Learning & Opponent Memory

## Maç sonrası öğrenme

Gerçek skor geldikten sonra sistem:

- 1X2 sonucunun doğru olup olmadığını ölçer
- Skor hatasını hesaplar
- xG sapmasını inceler
- Aşırı güveni tespit eder
- Kök nedenleri listeler
- Kalibrasyon ve veri güncelleme aksiyonları önerir

## Rakip hafızası

Aynı rakibe karşı geçmiş maçlardan:

- Gol ortalamaları
- Puan ortalaması
- İç/deplasman sayıları
- Maç oynaklığı

saklanır.

## Benzer maçlar

Yaklaşan maça yarışma, saha ve rakip eşleşmesine göre en benzer geçmiş maçlar
listelenir.
