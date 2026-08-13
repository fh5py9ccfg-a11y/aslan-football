# v3.5 Kubernetes, Cosign, SLO ve Runbook Denetimi

## Kubernetes manifest üretimi
Cluster manifest sözleşmesinden Namespace, Deployment ve Service belgeleri
üretilir. Container güvenlik bağlamı non-root, read-only root filesystem ve
privilege escalation kapalı olacak şekilde oluşturulur.

## Cosign sözleşmesi
Image doğrulaması digest, beklenen sertifika kimliği ve issuer ile yapılır.
Canlı sistemde verifier gerçek `cosign verify` veya Sigstore API çağrısına
bağlanmalıdır.

## Prometheus SLO adaptörü
Availability ve prediction pipeline başarı hedefleri için PromQL sorguları
üretilir ve SLO measurement sözleşmesine çevrilir.

## Kalıcı runbook denetimi
Runbook yürütmeleri SQLite üzerinde saklanabilir. Production ortamında bu depo
PostgreSQL'e taşınmalı ve değiştirilemez audit log ile desteklenmelidir.

## Yönetim görünümü
Runbook geçmişi execution, incident, operatör, durum ve tamamlanan adımlarla
yönetim ekranında sunulur.
