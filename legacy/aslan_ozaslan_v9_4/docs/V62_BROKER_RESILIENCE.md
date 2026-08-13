# v6.2 Broker Resilience

## Şema kayıt sistemi
Mesajlar isim ve sürüm üzerinden doğrulanır. Eksik veya yanlış alanlar işleme
girmeden reddedilir.

## Retry
Üstel geri çekilme uygulanır. Maksimum deneme sayısı dolunca mesaj tekrar
işlenmez ve dead-letter akışına bırakılır.

## Dead-letter replay
Hatalı mesajlar kontrollü biçimde `.retry` topic'ine yeniden yayımlanabilir.
Orijinal topic ve offset header olarak korunur.

## Sağlık kontrolü
Producer üzerinden sentetik bir sağlık mesajı gönderilir ve gecikme ölçülür.

## Kafka yapılandırması
Bootstrap server, client id, consumer group ve güvenlik protokolü doğrulanır.

## Üretim sınırı
Gerçek broker bağlantısı için hâlâ dış ortam bilgileri gerekir. Bu sürüm,
bağlantı kurulduğunda kullanılacak güvenilirlik davranışlarını tamamlar.
