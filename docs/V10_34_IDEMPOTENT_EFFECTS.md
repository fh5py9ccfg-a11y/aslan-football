# v10.34 Idempotent Effects & Compensation

## Kalıcı idempotency key
Her closure dış etkisi request + claim kimliğinden türetilen kalıcı anahtarla
korunur. Aynı işlem tekrar çağrıldığında tamamlanan sonuç yeniden döndürülür.

## Kısmi başarısızlık
İşlem sırasında hata oluşursa effect FAILED olarak kaydedilir ve ayrı bir
compensation kaydı oluşturulur.

## Compensation yönetimi
Admin ve ops rolleri request bazında compensation kayıtlarını görebilir. Admin
tamamlanan telafi işlemini işaretleyebilir.

## Üretim sınırı
Compensation kaydı telafi ihtiyacını yönetir; gerçek geri alma operasyonu ilgili
dış sistem adaptörü tarafından uygulanmalıdır.
