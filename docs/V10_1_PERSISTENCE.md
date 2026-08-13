# v10.1 PostgreSQL Persistence & Outbox Worker

## API persistence
Üretim ve development ortamında event repository PostgreSQL kullanır.
Test ortamında hızlı ve izole in-memory repository seçilir.

## Atomik event + outbox
Match event ve outbox mesajı aynı SQLAlchemy session transaction'ında yazılır.
Duplicate fixture/sequence kaydı transaction'ı geri alır.

## Worker
Worker PostgreSQL `FOR UPDATE SKIP LOCKED` ile outbox mesajlarını güvenli biçimde
claim eder. Başarılı yayınlar `PUBLISHED`, geçici hatalar `RETRY`, sürekli
hatalar `DEAD_LETTER` olur.

## Geçici yayın hedefi
Publisher şu an konsola JSON yazar. Kafka, RabbitMQ veya Redis Streams publisher
adapter'ı sonraki aşamada bağlanacaktır.
