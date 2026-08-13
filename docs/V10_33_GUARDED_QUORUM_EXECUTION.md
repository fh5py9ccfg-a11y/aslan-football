# v10.33 Guarded Quorum Execution

## Otomatik heartbeat
Closure çalıştığı sürece execution lease arka planda yenilenir.

## Ownership kaybı
Heartbeat owner token'ın artık geçerli olmadığını görürse işlem sonucu Redis'e
commit edilmez.

## Stale commit koruması
Closure operasyonu tamamlanmış olsa bile execution ownership kaybedildiyse
`complete` çağrısı yapılmaz veya Redis tarafından reddedilir.

## Event loop izolasyonu
Senkron closure işlemi `asyncio.to_thread` üzerinde çalıştırılır; heartbeat event
loop içinde zamanında çalışmaya devam eder.

## Operasyonel metrik
Ownership kaybı ayrı Prometheus sayacıyla izlenir.

## Üretim sınırı
Dış sistemlerde geri alınamaz yan etkiler oluşursa yalnızca commit engeli yeterli
değildir. Sonraki adım idempotency key ve compensating action desteğidir.
