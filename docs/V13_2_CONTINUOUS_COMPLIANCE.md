# v13.2 Continuous Compliance Monitoring

## Compliance snapshots

Governance coverage, framework coverage, exception health ve evidence coverage
tek tenant compliance score içinde birleştirilir.

## Drift detection

Önceki snapshot ile yeni snapshot karşılaştırılarak score drop, evidence
coverage drop ve yeni compliance gap olayları üretilir.

## Remediation

Her drift için assignee, due date, action type ve yaşam döngüsü taşıyan
remediation action oluşturulur.

## Timeline

Snapshot, drift ve remediation olayları tenant bazında tek zaman çizelgesinde
sunulur.
