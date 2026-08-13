# v9.4 Transactional Outbox & Worker Coordination

## Transactional outbox
Provider raw archive kaydı ile yayınlanacak outbox mesajı aynı SQLite
transaction içinde yazılır.

## Worker lease
Mesajlar süreli lease ile tek worker'a atanır. Aynı mesaj eş zamanlı iki worker
tarafından alınamaz.

## Retry
Yayın hataları exponential backoff ile yeniden denenir.

## Dead letter
Maksimum deneme sayısını aşan mesajlar dead-letter durumuna taşınır.

## Recovery
Süresi dolan PROCESSING lease'leri tekrar RETRY durumuna alınabilir.

## Üretim sınırı
SQLite tek düğüm koordinasyonu sağlar. Çok düğümlü üretimde PostgreSQL
SKIP LOCKED veya broker-native delivery semantiği tercih edilmelidir.
