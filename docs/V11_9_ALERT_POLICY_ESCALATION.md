# v11.9 Alert Policy, Escalation & Acknowledgement

## Alert policies

Tenant ve trigger bazında minimum severity, dedup penceresi, acknowledge SLA ve
escalation target tanımlanır.

## Silence rules

Belirli zaman aralığında tenant, match veya trigger bazında incident üretimi
bastırılabilir.

## Deduplication

Aynı match ve trigger için tanımlı pencere içinde ikinci incident açılmaz.

## Incident lifecycle

OPEN → ACKNOWLEDGED → RESOLVED durumları desteklenir.

## Escalation

Acknowledge SLA süresi aşılan açık incident'lar on-call hedefe yükseltilir.
