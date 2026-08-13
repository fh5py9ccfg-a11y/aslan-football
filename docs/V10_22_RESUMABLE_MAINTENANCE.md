# v10.22 Resumable Maintenance

## Cursor checkpoint
Bakım turu subject/family fazını ve Redis SCAN cursor değerini fencing korumalı
progress kaydında saklar.

## Kaldığı yerden devam
Batch veya zaman bütçesi dolduğunda sonraki tur son kaydedilen cursor ve fazdan
devam eder.

## Bounded work
Her tur maksimum indeks sayısı ve süre bütçesiyle sınırlandırılır. Böylece bakım
işi API instance kaynaklarını uzun süre işgal etmez.

## Güvenli progress yazımı
Daha düşük fencing token taşıyan eski lider progress checkpoint'ini
değiştiremez.

## Metrikler
Zaman bütçesi ve batch sınırına ulaşan bakım turları ayrı sayaçlarla izlenir.
