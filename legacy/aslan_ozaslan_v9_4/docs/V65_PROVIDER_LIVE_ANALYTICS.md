# v6.5 Provider to Live Analytics

## Köprü
Sportmonks'tan normalize edilen canlı fixture ortak provider snapshot nesnesine
dönüştürülür.

## State guard
Dakika gerilemesi, skor gerilemesi, geçersiz skor ve canlı olmayan fixture
güncellemeleri reddedilir.

## Event türetme
Snapshot skor farkından deterministik gol eventleri türetilir. Event kimlikleri
fixture ve skor seviyesine göre oluşturulur.

## Orchestrator
Provider snapshot, event store ve canlı olasılık güncelleyici tek akışta
birleştirilir.

## Kalıcılık
Son kabul edilen fixture snapshot atomik JSON yazımıyla saklanır.

## Üretim sınırı
Snapshot farkından yalnızca skor eventleri güvenilir biçimde türetilebilir.
Kart, şut, oyuncu değişikliği ve diğer olaylar provider event listesinden
doğrudan alınmalıdır.
