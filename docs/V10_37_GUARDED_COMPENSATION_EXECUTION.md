# v10.37 Guarded Compensation Execution

## Otomatik heartbeat
Compensation handler çalıştığı sürece execution lease arka planda yenilenir.

## Ownership kaybı
Heartbeat owner token'ın geçersiz olduğunu görürse handler sonucu iş kaydına
commit edilmez; retry veya dead-letter durumu yazılmaz.

## Stale worker koruması
Takeover sonrasında eski worker execution complete veya business completion
yapamaz.

## Async worker entegrasyonu
Compensation worker handler'ları event loop dışında çalıştırır; heartbeat event
loop üzerinde zamanında devam eder.

## Operasyonel metrik
Ownership kaybı ayrı Prometheus sayacıyla izlenir.
