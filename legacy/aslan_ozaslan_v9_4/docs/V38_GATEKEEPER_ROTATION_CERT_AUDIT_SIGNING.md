# v3.8 Gatekeeper, Rotation, Certificate ve Paket İmzalama

## Gatekeeper uyumluluğu
ConstraintTemplate ve Constraint belgeleri üretilebilir. İlk politika,
Deployment image'larının digest ile sabitlenmesini zorunlu kılar.

## Secret rotation
Her secret için rotasyon sıklığı ve overlap penceresi tanımlanır. Eski secret
yenisi devreye girdikten sonra kontrollü biçimde emekliye ayrılır.

## Certificate expiry
Sertifika bitiş tarihi warning ve critical eşiklerine göre izlenir.

## PostgreSQL append-only audit
PostgreSQL audit sözleşmesi update/delete yetkilerinin kaldırılması, ayrı
append-only rolü, RLS, zincir doğrulama ve WORM export gerektirir.

## Deployment bundle signing
Canonical deployment manifest seti tek digest altında imzalanır. Belgelerdeki
herhangi bir değişiklik imza doğrulamasını bozar.
