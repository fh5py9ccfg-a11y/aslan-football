# v12.0 Incident Postmortem & Operational Knowledge Base

## Incident bağlantısı

Her postmortem mevcut alert incident kaydından oluşturulur ve incident kimliğiyle
tekilleştirilir.

## Optimistic concurrency

Her değişiklik revision numarasıyla korunur. Eski revision ile yapılan yazma
girişimleri reddedilir.

## Evidence ve action items

Metric, log, trace ve deployment kanıtları ile sahip, termin ve tamamlanma durumu
bulunan aksiyonlar saklanır.

## Yayın kapısı

Incident RESOLVED olmadan; root cause, impact, evidence ve action item
tamamlanmadan postmortem yayınlanamaz. Yayınlanan kayıt değiştirilemez.

## Benzer incident arama

Yayınlanmış postmortem'lar kök neden, etki, dersler ve katkı faktörleri üzerinden
token benzerliğiyle aranır.
