# v10.40 Production Outbox Transport

## Transport sözleşmesi
Her transport publish çağrısında event ID, destination, external message ID,
payload SHA-256 ve kabul durumunu içeren receipt üretir.

## Webhook adaptörü
Webhook transport Idempotency-Key, X-Event-Id ve X-Payload-SHA256 başlıklarını
gönderir. Yalnızca 2xx yanıtlar başarılı kabul edilir.

## Receipt kalıcılığı
Başarılı delivery acknowledgement öncesinde publish receipt Redis'e kaydedilir.

## Güvenlik
Transport tarafından dönen event ID kaynak event ID ile eşleşmezse teslimat
başarılı sayılmaz ve retry akışına girer.

## Üretim sınırı
Webhook authorization değeri environment secret olarak sağlanmalıdır. Uzun
vadede Kafka/NATS adaptörleri aynı transport sözleşmesine eklenebilir.
