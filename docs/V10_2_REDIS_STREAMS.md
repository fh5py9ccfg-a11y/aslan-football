# v10.2 Redis Streams Messaging

## Publisher
PostgreSQL outbox worker mesajları Redis Streams'e yayınlar.

## Consumer group
Tüketiciler consumer group üzerinden mesaj okur ve başarılı işlemlerden sonra
ACK gönderir.

## Idempotent consumption
Her consumer group ve message ID çifti PostgreSQL receipt tablosunda tekil olarak
saklanır. Aynı mesaj yeniden teslim edilirse iş mantığı tekrar çalıştırılmaz.

## Test yaklaşımı
Birim testlerde gerçek Redis yerine protokolü taklit eden deterministik fake
client kullanılır. Gerçek Redis container testi Docker ortamında ayrıca
çalıştırılmalıdır.
