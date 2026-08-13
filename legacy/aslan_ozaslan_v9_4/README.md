# Aslan Özaslan v9.4

Transactional Outbox ve güvenli worker koordinasyonu.

## Eklenenler
- SQLite transactional outbox
- Archive + outbox atomik transaction
- Lease tabanlı message claim
- Eşzamanlı worker çakışma engeli
- Publish state yönetimi
- Exponential retry
- Dead-letter akışı
- Süresi dolmuş lease recovery
- Outbox Operations yönetim ekranı

## Dürüst üretim durumu
Tek düğümlü güvenli koordinasyon hazırdır. Çok düğümlü üretimde PostgreSQL
SKIP LOCKED veya broker-native delivery kullanımı gerekir.
