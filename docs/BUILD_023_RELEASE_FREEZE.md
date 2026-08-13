# Build 023 — Release Freeze

## Production preflight

Kontroller:

- Zorunlu ortam değişkenleri
- Güçlü secret değerleri
- Veritabanı
- Redis
- Backup
- Observability

## Migration preflight

Kaynak ve hedef schema alanları karşılaştırılır. Alan silme işlemleri
destructive change olarak işaretlenir ve migration BLOCKED olur.

## Disaster recovery drill

- Backup checksum
- Schema doğrulaması
- Zorunlu bölümler
- Smoke test
- RTO ve RPO hedefleri

## İmzalı manifest

Release manifesti; paket checksum, kaynak manifest checksum ve kabul
fingerprint'iyle imzalanır.
