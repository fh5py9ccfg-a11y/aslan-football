# v10.17 Indexed Session Revocation

## Redis family index
Her refresh token family için `family → session_id` seti tutulur.

## Redis subject index
Her kullanıcı için `subject → session_id` seti tutulur.

## Atomik family revocation
Refresh reuse algılandığında Lua script ilgili family setindeki tüm session
kayıtlarını aynı Redis işlemi içinde iptal eder.

## SCAN kaldırıldı
Family ve subject iptal yollarında Redis SCAN kullanılmaz. İptal maliyeti yalnızca
ilgili kullanıcı veya family içindeki oturum sayısıyla orantılıdır.

## Üretim sınırı
Session kayıtları TTL ile silindiğinde indeks setlerinde kısa süreli orphan
session ID kalabilir. Listeleme bunları yok sayar; periyodik index cleanup sonraki
bakım adımıdır.
