# v12.2 SLO-Aware Release Guard

## Release policy

Tenant bazında minimum reliability score, warning ve critical error-budget
davranışı ile override gereksinimleri tanımlanır.

## Gate evaluation

Her release, tenant reliability score ve aktif SLO durumlarıyla değerlendirilir.
Kritik error-budget ihlali veya düşük reliability score yayın dondurabilir.

## Controlled override

Yetkili operatör açıklayıcı bir neden sunarak gate kararını override edebilir.
Aktör, neden ve karar sonucu kalıcı audit kaydında tutulur.

## History

Tüm gate değerlendirmeleri tenant bazında zaman sıralı olarak sorgulanabilir.
