# v10.15 Resilient OIDC Metadata

## Stale-if-error
Discovery ve JWKS cache süreleri dolduktan sonra sağlayıcı geçici olarak
ulaşılamazsa sınırlı süreyle son başarılı veri kullanılabilir.

## Circuit breaker
Art arda metadata hataları dış çağrıları geçici olarak durdurur. Recovery süresi
sonunda half-open deneme yapılır.

## Background refresh
Discovery ve JWKS metadata belirli aralıklarla arka planda yenilenir. Uygulama
kapanışında görev kontrollü biçimde durdurulur.

## Cache health
Admin ve ops rolleri discovery/JWKS cache durumunu, son başarıyı ve son hatayı
görebilir.

## Güvenlik sınırı
Stale süreleri dikkatli seçilmelidir. Çok uzun stale JWKS süresi iptal edilmiş
veya döndürülmüş anahtarların gereğinden uzun kabul edilmesine yol açabilir.
