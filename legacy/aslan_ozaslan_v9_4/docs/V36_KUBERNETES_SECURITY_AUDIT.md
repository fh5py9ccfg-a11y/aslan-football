# v3.6 Kubernetes Güvenliği ve Audit

## Secret ve ConfigMap
Secret değerleri Kubernetes Secret belgesinde base64 biçiminde üretilir.
Bu şifreleme değildir; canlı sırlar dış sır yöneticisinden sağlanmalıdır.

## Network policy
Varsayılan deny policy ve açık servisler arası allow kuralları üretilir.
Bu yaklaşım gereksiz doğu-batı trafiğini sınırlar.

## Ingress ve TLS
Ingress yalnızca TLS secret ile üretilir ve SSL redirect zorunludur.

## Audit deposu
Yönetim işlemleri aktör, eylem, kaynak ve payload ile kalıcı kaydedilir.
Canlı ortamda PostgreSQL ve append-only audit politikası kullanılmalıdır.

## Bundle doğrulaması
Namespace, Deployment, Service, Ingress ve NetworkPolicy zorunludur.
Deployment image'ları digest ile sabitlenmemişse paket geçersiz sayılır.
