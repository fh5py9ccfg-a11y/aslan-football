# v11.5 Real-Time Inference Platform

## Model warm-up

Model runtime kayıtları COLD, READY veya FAILED durumlarıyla izlenir. Trafiğe
girmeden önce explicit warm-up yapılabilir.

## Adaptive routing

Deployment slot'undaki champion model primary olarak, önceki champion fallback
olarak seçilir. Batch profili varsa challenger'a yönlenebilir.

## Prediction cache

Tenant, model ve canonical feature hash üzerinden cache anahtarı üretilir.

## Timeout ve fallback

Primary model timeout veya readiness hatası üretirse önceki champion'a geçilir.

## Explainability

İstek bazında en etkili sayısal feature'lar açıklama çıktısına eklenir.

## Micro-batching

İstekler konfigüre edilebilir küçük gruplar halinde paralel işlenir.
