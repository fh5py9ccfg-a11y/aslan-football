# v12.3 Progressive Delivery & Automatic Rollback

## Canary plans

Her release için artan trafik yüzdelerinden oluşan rollout aşamaları tanımlanır.
Son aşama zorunlu olarak yüzde 100'dür.

## Start gate

Rollout başlamadan önce mevcut SLO-aware release guard değerlendirilir.

## Quality gates

Her canary aşamasında tenant reliability score, warning SLO sayısı ve critical
SLO sayısı kontrol edilir.

## Promote, pause, rollback

Kalite kapıları geçilirse bir sonraki aşamaya terfi edilir. İhlalde politika
tercihine göre rollout duraklatılır veya otomatik rollback durumuna geçirilir.

## Audit history

Her değerlendirme, kullanılan metrikler, karar, neden ve aşama yüzdesiyle
saklanır.
