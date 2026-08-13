# v9.2 Sportmonks Provider Payload Gateway

## Şema doğrulama
Fixture, player ve event payloadları zorunlu alanlar, dakika sınırları ve event
türü bakımından doğrulanır.

## Normalizasyon
Sportmonks yapıları ortak fixture, player ve event modellerine dönüştürülür.

## Karantina
Geçersiz veya normalize edilemeyen kayıtlar hata ve uyarılarıyla birlikte
kalıcı karantina deposuna yazılır.

## Decision context bridge
Normalize edilmiş ve doğrulanmış veriler Football OS karar bağlamlarına
dönüştürülebilir.

## Üretim sınırı
Gerçek endpoint sürümleri ve Sportmonks plan kapsamı token ile smoke test
edilmeden tüm alanların erişilebilir olduğu varsayılmaz.
