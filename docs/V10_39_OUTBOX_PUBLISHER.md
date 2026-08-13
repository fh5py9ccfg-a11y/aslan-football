# v10.39 Compensation Outbox Publisher

## Teslimat claim'i
Her outbox event'i yayımlanmadan önce Redis delivery lease alınır. Aynı event
birden fazla publisher tarafından eşzamanlı yayımlanamaz.

## Idempotent event kimliği
Event ID kalıcıdır. DELIVERED durumundaki event tekrar işlenmez.

## Retry ve dead-letter
Geçici broker hatalarında exponential backoff uygulanır. Maksimum deneme sonrası
delivery DEAD_LETTER durumuna taşınır.

## Worker
Outbox publisher uygulama lifecycle ile başlar ve belirlenen batch boyutunda
olayları işler.

## Üretim sınırı
Varsayılan transport log tabanlıdır. Kafka, NATS veya webhook transport adaptörü
bağlanmadan olaylar dış sisteme teslim edilmiş sayılmamalıdır.
