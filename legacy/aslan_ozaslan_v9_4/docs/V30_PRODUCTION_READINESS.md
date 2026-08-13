# v3.0 Üretim Hazırlığı

## Yapılandırma doğrulama
Production ortamında PostgreSQL, Redis, güçlü session secret, güçlü backup key ve
HTTPS zorunludur. Eksik ayarlarla süreç başlatılmamalıdır.

## Gerçek kilit adaptörleri
Redis ve PostgreSQL advisory lock sözleşmeleri eklendi. Test uygulamaları gerçek
istemci olmadan davranışı doğrular.

## Alarm çıkışları
Webhook ve e-posta sink sözleşmeleri alarm yönlendirme katmanına bağlanabilir.
Başarısız webhook çağrısı sessizce başarılı sayılmaz.

## Kimlik doğrulamalı admin route
Admin erişimi aktif oturum ve MANAGE_DATA yetkisi ister. GET dışındaki isteklerde
CSRF doğrulaması zorunludur.

## Üretim hazır olma raporu
Kritik kontroller blocker, ikincil kontroller warning olarak sınıflandırılır.
Ağırlıklı bir hazırlık puanı üretilir; blocker varsa sistem ready değildir.
