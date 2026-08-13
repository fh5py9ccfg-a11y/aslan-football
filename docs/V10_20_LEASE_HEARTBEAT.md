# v10.20 Lease Heartbeat & Safe Abort

## Heartbeat
Bakım worker'ı lease TTL dolmadan düzenli Redis renew çağrısı yapar.

## Lease kaybı
Renew başarısız olursa heartbeat lease kaybını işaretler. Maintainer tarama ve
üye işleme noktalarında checkpoint kontrolü yapar.

## Güvenli abort
Lease kaybı sonrası bakım turu mümkün olan ilk güvenli checkpoint'te durur ve
rapor `lease_lost=true`, `aborted=true` olarak işaretlenir.

## Thread izolasyonu
Senkron Redis bakım işlemi event loop'u bloke etmemesi için `asyncio.to_thread`
üzerinde çalıştırılır.

## Metrikler
Lease kaybı ve abort olayları ayrı Prometheus sayaçlarıyla izlenir.

## Üretim sınırı
Tek bir Redis komutu çok uzun sürerse checkpoint ancak komut tamamlandıktan sonra
çalışır. SCAN count düşük tutulduğu için kesme gecikmesi sınırlıdır.
