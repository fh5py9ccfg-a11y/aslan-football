# v2.8 Zamanlama, Kurtarma ve Metrikler

## Görev zamanlayıcı
Sabit aralıklı görevler tekrar eden işler için kayıt edilir. Aynı zaman
penceresinde görev ikinci kez kuyruğa eklenmez.

## Kilit kurtarma
Worker çökerse RUNNING durumda kalan görevler belirlenen kilit süresi dolduğunda
yeniden PENDING durumuna alınır. Maksimum deneme sınırına ulaşmış işler kurtarılmaz.

## Dead-letter görünümü
DEAD durumundaki işler hata ve deneme sayısıyla yönetim katmanından listelenebilir.

## Şifreli yedekleme
Yedek dosyaları bütünlük etiketiyle korunur. Yanlış anahtar veya bozulmuş dosya
geri yüklenemez. Canlı ortamda anahtar uygulama kodunda değil, sır yöneticisinde
saklanmalıdır.

## Merkezi metrikler
Counter ve gauge türleri ilk operasyon metrik sözleşmesini oluşturur. Sonraki
aşamada Prometheus/OpenTelemetry adaptörü bu sözleşmeye bağlanabilir.
