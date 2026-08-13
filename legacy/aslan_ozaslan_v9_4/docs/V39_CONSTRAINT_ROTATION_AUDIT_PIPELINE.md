# v3.9 Constraint Set, Rotation, Audit ve İmzalı Pipeline

## Production constraint set
Immutable image, non-root, read-only root filesystem, kaynak limitleri ve health
probe kuralları tek production constraint setinde toplanır.

## Secret rotation yürütme
Rotasyon zamanı geldiğinde yeni sürüm oluşturulur, aktif edilir ve politika izin
veriyorsa eski sürüm kontrollü biçimde emekliye ayrılır.

## Sertifika olay geçmişi
ISSUED, RENEWED, FAILED ve EXPIRING olayları ayrı kayıtlar olarak izlenir.

## Audit doğrulama işi
Append-only audit hash zinciri periyodik bir iş olarak doğrulanabilir. Zincir
bozulursa işlem başarısız raporlanır.

## İmzalı deployment pipeline
Deployment bundle hem içerik kurallarından hem imza doğrulamasından geçmelidir.
Bu iki kontrolden biri başarısızsa release engellenir.
