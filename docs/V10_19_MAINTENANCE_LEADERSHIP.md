# v10.19 Maintenance Leadership

## Dağıtık lease
Birden fazla API instance'ı çalışırken yalnızca Redis lease'i alan instance bakım
turunu yürütür.

## Güvenli release
Lease yalnızca kendi owner ID'sine sahip worker tarafından Lua ile yenilenebilir
ve bırakılabilir.

## Jitter ve backoff
Başarılı bakım turlarından sonra jitter uygulanır. Hata durumunda ayrı backoff
süresi kullanılır.

## Prometheus metrikleri
Bakım turu, atlanan tur, hata, temizlenen orphan ve TTL onarımı sayaçları
yayınlanır.

## Üretim sınırı
Bakım turu lease TTL süresinden uzun sürerse lease yenileme gerekir. Mevcut indeks
hacmi için TTL geniş tutulmuştur; sonraki adım heartbeat tabanlı otomatik lease
yenilemedir.
