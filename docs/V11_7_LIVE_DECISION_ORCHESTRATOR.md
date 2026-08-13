# v11.7 Live Decision Orchestrator

## Streaming-to-inference bridge

Streaming snapshot; xG, momentum, possession trend, anomaly score ve event count
feature'larına dönüştürülerek gerçek zamanlı inference isteğine bağlanır.

## Idempotency

Match ID, trigger ve event time birleşiminden deterministik decision ID üretilir.
Aynı canlı karar iki kez yürütülemez.

## Cooldown

Aynı maç ve trigger için kısa süre içinde tekrar inference çalıştırılması
engellenir.

## Retry

Inference geçici hata üretirse sınırlı sayıda güvenli retry uygulanır.

## Audit record

Model ID, prediction, confidence, fallback bilgisi, explanation ve kullanılan
feature snapshot kalıcı karar kaydında tutulur.
