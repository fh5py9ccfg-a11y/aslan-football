# Model Drift İzleme

İlk drift mekanizması doğruluk düşüşünü izler.

- Baseline performans ile son dönem performansı karşılaştırılır.
- Belirlenen eşik aşılırsa alarm oluşur.
- Alarm modelin otomatik yayınlanması anlamına gelmez.
- Yeni model ancak backtest, kalibrasyon ve yayın öncesi kontrollerden geçerse CHAMPION olabilir.

Sonraki sürümlerde log-loss, Brier score ve kalibrasyon drift ölçümleri eklenecektir.
