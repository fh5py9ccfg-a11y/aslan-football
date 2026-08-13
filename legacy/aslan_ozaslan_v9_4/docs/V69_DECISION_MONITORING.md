# v6.9 Real-Time Decision Monitoring

## Kalite penceresi
Karar güveni, risk, fırsat, gecikme ve degraded durumu sınırlı zaman penceresinde
saklanır.

## Drift
Baseline ve recent karar pencereleri; güven düşüşü, risk artışı ve gecikme
regresyonu bakımından karşılaştırılır.

## Circuit breaker
Drift veya yüksek degraded oranı art arda görülürse canlı karar circuit'i açılır.

## Safe mode
Circuit açıkken sistem yalnızca read-only, historical analysis ve manual review
işlemlerine izin verir.

## P95 gecikme
Canlı karar gecikmesi P95 üzerinden izlenir.

## Üretim sınırı
Safe mode otomatik finansal veya harici işlem yapmaz; yalnızca karar destek
özelliklerini sınırlar.
