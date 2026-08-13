# v10.41 Signed Webhook & Circuit Breaker

## HMAC imzası
Webhook payload'ı timestamp + event ID + canonical JSON gövdesi üzerinden
HMAC-SHA256 ile imzalanır.

## Replay koruması
X-Webhook-Timestamp ve Idempotency-Key başlıkları alıcı tarafın tekrar oynatma
ve yinelenen teslimat kontrolleri yapmasını sağlar.

## Circuit breaker
Ardışık hatalar threshold'u aşınca transport OPEN durumuna geçer. Recovery süresi
sonunda tek half-open probe yapılır; başarıda kapanır, hatada yeniden açılır.

## Operasyonel görünürlük
Admin/ops transport sağlık durumunu görebilir. Yalnızca admin manuel reset
yapabilir.
