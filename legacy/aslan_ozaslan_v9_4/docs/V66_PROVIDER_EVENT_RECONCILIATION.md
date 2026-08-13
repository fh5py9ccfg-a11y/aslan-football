# v6.6 Provider Event Reconciliation

## Doğrudan event mapping
Provider goal, shot, card, dangerous attack ve substitution olayları ortak
LiveMatchEvent nesnesine dönüştürülür.

## Event repository
Provider eventleri fixture ve provider event kimliğiyle saklanır. Aynı payload
yeniden gelirse tekrar işlenmez.

## Geç olay
Geç gelen eventler kabul edilir; tolerans penceresini aşarsa replay gerektirir.

## Correction ve cancellation
Düzeltilmiş event farklı kimlik sürümüyle işlenir. İptal edilen event canlı akışa
aktarılmaz.

## Reconciliation
Snapshot skoru ile aktif goal event sayıları karşılaştırılır. Uyuşmazlık ayrı
raporlanır ve gizlenmez.

## Üretim sınırı
Tam replay için live processor state'inin event ledger üzerinden baştan
kurulması gerekir. Bu sürüm replay ihtiyacını işaretler, otomatik tam replay'i
bir sonraki katmana bırakır.
