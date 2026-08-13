# v10.11 Credential Hardening

## Direct API key lookup
Provider istekleri `X-API-Key-ID` ve `X-API-Key` taşır. Registry doğrudan key ID
ile kayıt okur; doğrulama sırasında Redis SCAN yapılmaz.

## Rotation grace
API key rotation sırasında eski secret için en fazla bir saatlik kontrollü geçiş
süresi tanımlanabilir.

## Atomic WebSocket ticket
Redis Lua script `GET + DEL` işlemini tek atomik adımda yapar. Aynı ticket iki
instance tarafından eş zamanlı tüketilemez.

## Üretim sınırı
API key listeleme işlemi Redis SCAN kullanmaya devam eder; yalnızca admin
operasyonudur ve request doğrulama yolunda kullanılmaz.
