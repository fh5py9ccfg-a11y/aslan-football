# v10.25 Journal Recovery & Poison Index Isolation

## Claim heartbeat
Uzun süren indeks işlemleri claim TTL dolmadan heartbeat ile uzatılabilir.

## Expired claim takeover
Claim süresi dolmuşsa daha yüksek fencing token taşıyan yeni lider aynı işi
devralabilir. Aktif claim başka owner tarafından alınamaz.

## Attempt tracking
Her devralma claim attempt sayısını artırır.

## Quarantine
Aynı indeks belirlenen sayıda başarısız olursa karantinaya alınır. Bakım turu
bu indeksi atlayıp diğer indekslerle devam eder.

## Operasyonel görünürlük
Admin ve ops rolleri karantinadaki indeksleri, hata mesajını ve attempt sayısını
görebilir.

## Güvenlik sınırı
Karantinaya alınan indeksler otomatik düzeltilmez; inceleme ve kontrollü retry
işlemi sonraki yönetim adımıdır.
