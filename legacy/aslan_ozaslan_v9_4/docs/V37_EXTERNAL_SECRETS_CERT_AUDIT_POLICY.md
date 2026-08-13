# v3.7 External Secrets, Certificate, Audit Zinciri ve Policy-as-Code

## External Secrets
Canlı sırlar Kubernetes manifestine gömülmez. ExternalSecret belgesi yalnızca
harici sır yöneticisindeki anahtar ve property referanslarını taşır.

## Certificate Manager
TLS sertifikası Certificate kaynağıyla üretilir. Private key rotation policy
Always olarak tanımlanır.

## Append-only audit
Audit kayıtları önceki kaydın hash'ini içerir. Zincirdeki bir kayıt değiştirilirse
bütünlük doğrulaması başarısız olur. Production ortamında aynı model PostgreSQL
ve WORM depolama ile güçlendirilmelidir.

## Policy-as-code
Deployment kararı kodlanmış kurallarla verilir:
- immutable image,
- production replica sayısı,
- TLS,
- external secrets,
- network policy.

Blocker başarısızsa deployment engellenir; warning yalnızca raporlanır.

## Yönetim görünümü
Policy blocker ve uyarıları tek ekranda görünür.
