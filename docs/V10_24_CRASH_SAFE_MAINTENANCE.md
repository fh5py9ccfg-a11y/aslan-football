# v10.24 Crash-Safe Maintenance

## Claim journal
Her indeks işlenmeden önce fencing korumalı kısa ömürlü claim oluşturulur.

## Complete marker
İndeks mutasyonu tamamlandığında durable complete marker yazılır ve claim
silinir. Progress güncellemesi sonradan başarısız olsa bile tekrar denemede
complete marker görülür ve mutasyon yinelenmez.

## Idempotent recovery
Process mutasyon ile checkpoint arasında çökerse pending key sonraki turda tekrar
görülür; journal tamamlanmış kaydı sayesinde güvenle atlanır.

## Recoverable claims
Admin ve ops kullanıcıları hâlen claim durumunda kalan bakım işlemlerini
görebilir.

## Üretim sınırı
Complete marker TTL süresi, progress'in olası geri kalma süresinden uzun
tutulmalıdır. Varsayılan bir gündür.
