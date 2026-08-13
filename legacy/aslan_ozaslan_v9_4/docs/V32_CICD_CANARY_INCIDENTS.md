# v3.2 CI/CD, Canary ve Incident Yönetimi

## Deployment pipeline
Pipeline aşamaları kritik ve ikincil olarak ayrılır. Kritik aşama başarısız olursa
sonraki deployment adımları çalıştırılmaz.

## Canary release
Yeni sürüm yalnızca minimum trafik örneği, kabul edilebilir hata oranı ve p95
gecikme sınırlarını geçtiğinde promote edilir.

## Ortam kayıt defteri
Development, test, staging ve production ortamları açıkça tanımlanır. Production
en az iki replica gerektirir.

## Migration gate
Production migrasyonlarında sürüm çakışması, eksik checksum, yanlış sıra ve
geri döndürülemez değişiklikler release'i engeller.

## Incident yönetimi
SEV1, SEV2 ve SEV3 olayları OPEN, MITIGATED ve RESOLVED yaşam döngüsüyle izlenir.
Çözümlenmiş olay sessizce yeniden açılamaz; yeni incident oluşturulmalıdır.
