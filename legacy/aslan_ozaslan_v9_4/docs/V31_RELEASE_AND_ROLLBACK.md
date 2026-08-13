# v3.1 Release ve Rollback Katmanı

## Release artifact
Her release dosyası sürüm, oluşturulma zamanı ve SHA-256 özetiyle kayıt altına
alınır. Dosya değişirse doğrulama başarısız olur.

## Rollback
Rollback planı uygulama sürümünü geri almanın yanında veritabanı uyumluluğunu,
smoke testlerini, trafiği geri açmayı ve hata izlemesini zorunlu kılar.

## Sır yönetimi
Uygulama sır yöneticisine bağımlı olacak şekilde bir provider sözleşmesi kullanır.
Eksik veya kısa sırlarla production süreci başlatılmaz.

## Smoke test
Release sonrası sağlık, veritabanı ve kritik uçlar hızlı biçimde doğrulanır.
Başarısız smoke testi release'i başarılı saymaz.

## Release ekranı
Hazırlık raporu, blocker listesi, smoke testleri ve artifact özeti tek görünümde
birleştirilir.
