# v10.4 End-to-End Provider Pipeline

- Sportmonks fixture event senkronizasyonu
- JSON checkpoint ile kaldığı yerden devam
- `provider.events` Redis Stream yayını
- Consumer mesajını API match event'ine dönüştüren bridge
- Correlation ID taşıma
- Duplicate API event'lerinde 409'u başarılı idempotent sonuç sayma
- Prometheus metrik endpoint'i

Gerçek Redis/PostgreSQL container ve canlı Sportmonks token testi yapılmamıştır.
