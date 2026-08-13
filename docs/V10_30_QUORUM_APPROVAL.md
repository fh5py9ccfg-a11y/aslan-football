# v10.30 Quorum Approval

## Çoklu checker
Risk seviyesine göre 1–5 onay gereksinimi tanımlanabilir.

## Rol grubu şartı
Sadece sayı değil, belirlenen gruplardan en az bir onay da zorunlu tutulabilir.
Örneğin admin + security.

## Oy güvenliği
Aynı kullanıcı aynı talebe yalnızca bir kez oy verebilir. Talebi oluşturan kişi
oy kullanamaz.

## Karar
Tek bir ret oyu talebi reddeder. Quorum tamamlanınca doğrulanmış karantina
kapatma akışı yalnızca bir kez çalışır.

## Bütünlük
Her oy HMAC ile imzalanır ve sonradan değiştirilip değiştirilmediği doğrulanabilir.
