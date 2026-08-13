# v3.4 Scanner, Provenance ve Cluster Manifest

## Vulnerability scanner adaptörü
Scanner yalnızca digest ile sabitlenmiş image referansını tarar. Scanner kimliği
ve taranan image referansı sonuçta yeniden doğrulanır.

## Image provenance
Image, builder ve source revision birlikte imzalanır. Değiştirilmiş provenance
doğrulamadan geçmez. Canlı sistemde bu sözleşme Sigstore/Cosign benzeri bir
harici imza altyapısına bağlanmalıdır.

## Canlı SLO adaptörü
SLO ölçümleri gerçek veri kaynağından çekilirken kaynak kimliği, objective adı,
zaman penceresi ve ölçüm aralığı doğrulanır.

## Runbook geçmişi
Runbook çalıştırmaları operatör, tamamlanan adımlar ve sonuç durumuyla izlenir.
Tamamlanan runbook sonradan sessizce değiştirilemez.

## Cluster manifest
Namespace, servis adı, replica, digest sabitlenmiş image, port, readiness ve
liveness path zorunludur. Production servisleri en az iki replica kullanır.

## Güvenlik ekranı
Provenance durumu, scanner bulguları ve supply-chain release gate tek yönetim
görünümünde birleştirilir.
