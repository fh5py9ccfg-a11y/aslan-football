# v11.1 Provider Integration & Data Quality Gateway

## Provider adapters

Harici sağlayıcı event'leri ortak normalize edilmiş maç olayı sözleşmesine
dönüştürülür.

## Provider trust

Geçerli, duplicate ve conflict oranlarından dinamik provider trust score
hesaplanır.

## Multi-source reconciliation

Aynı olaya ait birden fazla sağlayıcı kaydı; provider güveni, veri kalite puanı
ve timestamp yakınlığına göre uzlaştırılır.

## Confidence adjustment

Tahmin confidence değeri provider güveni ve veri kalitesine göre aşağı yönlü
kalibre edilir.

## Operasyon görünürlüğü

Normalize endpoint'i, provider trust endpoint'i ve confidence adjustment
endpoint'i admin/ops kullanımına açılır.
