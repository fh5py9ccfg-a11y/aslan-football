# v2.7 Güvenilir Operasyon Katmanı

## Kalıcı iş kuyruğu
Görevler SQLite üzerinde kalıcıdır. Worker çökse bile PENDING ve DEAD durumları
kaybolmaz. Bir görev yalnızca bir worker tarafından kilitlenebilir.

## Dead-letter davranışı
Maksimum deneme sayısına ulaşan görev DEAD durumuna geçer. Sessizce sonsuz döngüye
girmez ve yönetim panelinden incelenebilir.

## Cache namespace
Önbellek anahtarları sürümlüdür. Veri formatı değiştiğinde namespace sürümü
artırılarak eski cache kayıtları güvenli biçimde devre dışı bırakılabilir.

## Sağlık kontrolleri
Kritik ve kritik olmayan bağımlılıklar ayrılır. Kritik servis arızası sistemi
hazır değil durumuna geçirir; küçük görsel eksikler yalnızca degraded sayılır.

## Yedekleme
Dosya yedeği kopyalama sonrası SHA-256 ve boyut kontrolüyle doğrulanır.
Doğrulanmamış yedek başarılı kabul edilmez.
