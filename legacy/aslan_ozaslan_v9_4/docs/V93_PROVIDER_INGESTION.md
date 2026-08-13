# v9.3 Provider Ingestion Orchestrator

## İdempotency
Provider, payload türü, dış kimlik ve içerik hash'i üzerinden aynı kayıt ikinci
kez işlenmez.

## Raw archive
Doğrulanmış ham payloadlar içerik hash'iyle kalıcı ve tekrarsız biçimde
arşivlenir.

## Event projection
Doğrulanan provider eventleri append-only domain event store'a aktarılır.

## Karantina
Şema doğrulamasından geçmeyen payloadlar arşiv veya projection adımına
ulaşmadan karantinaya alınır.

## Checkpoint
Sayfalı senkronizasyonlarda cursor ve toplam işlenen kayıt sayısı saklanır.

## Üretim sınırı
Yerel SQLite ve JSON depoları tek süreçli temel sağlar. Dağıtık transaction,
outbox ve çoklu worker koordinasyonu sonraki sertleştirme katmanıdır.
