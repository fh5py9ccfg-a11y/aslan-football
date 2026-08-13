# v2.9 Gözlemlenebilirlik, Alarm ve Dağıtık Kilit

## Prometheus çıktısı
Merkezi metrik kayıt defteri Prometheus metin formatına dönüştürülebilir.
Metrik isimleri doğrulanır; sayısal olmayan değerler reddedilir.

## Telemetry
İlk OpenTelemetry uyum katmanı bounded event buffer sağlar. Bu katman daha sonra
gerçek span ve exporter adaptörlerine bağlanabilir.

## Alarm yönlendirme
Alarm şiddetine göre farklı sink'lere gönderim yapılır. Deduplication key aynı
alarmın kısa sürede tekrar tekrar gönderilmesini önler.

## Dağıtık kilit
Scheduler ve singleton işler için ortak kilit sözleşmesi eklendi. In-memory
uygulama yalnızca test ve geliştirme içindir; canlı ortamda Redis/PostgreSQL
uygulaması kullanılmalıdır.

## Dead-letter yeniden çalıştırma
DEAD durumundaki iş açık bir yönetim aksiyonuyla tekrar PENDING durumuna alınabilir.

## Operasyon ekranı
Metrikler, sağlık kontrolleri ve dead-letter işleri tek HTML görünümünde birleşir.
