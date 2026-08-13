# Mimari

## Katmanlar

1. Veri toplama
2. Veri doğrulama
3. Özellik üretimi
4. Tahmin motoru
5. Sunum

## Kritik kurallar

- Takıma özel veri eşiği sağlanmıyorsa tahmin üretme.
- Maç kimliği olmayan sonucu önbelleğe alma.
- Aynı önbellek anahtarını iki farklı maçta kullanma.
- Veri kaynağı çevrimdışıysa sabit yüzdeye düşme.
- Her sonuç model sürümü ve hesaplama kimliği taşısın.

## Önbellek anahtarı

`prediction:{competition_id}:{season}:{fixture_id}:{model_version}`

## Yayın akışı

Kod değişikliği → otomatik test → test ortamı → elle doğrulama → canlı yayın → geri dönüş noktası.
