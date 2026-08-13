# v10.28 Verified Quarantine Closure

## Retry sonrası doğrulama
Retry öncesi ve sonrası orphan sayısı, canlı session sayısı ve indeks TTL değeri
karşılaştırılır.

## Sağlık kanıtı
Sonuç; operatör, fencing token, önce/sonra metrikleri ve doğrulama gerekçesiyle
Redis remediation evidence kaydına yazılır.

## Doğrulanmış kapatma
Karantina yalnızca retry başarılı, orphan sayısı sıfır ve canlı indeks TTL değeri
geçerliyse kapatılır.

## Idempotency
Daha önce doğrulanmış evidence varsa tekrar retry çalıştırılmaz. Karantina kaydı
önceden kaldırılmışsa kapatma tamamlanmış kabul edilir.

## Üretim sınırı
Kapatma sonrası indeks progress kuyruğuna yeniden eklenir; normal bakım turu
durumu tekrar doğrular.
