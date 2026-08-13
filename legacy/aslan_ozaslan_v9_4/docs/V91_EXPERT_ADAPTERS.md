# v9.1 Football OS Expert Adapters

## Adapter katmanı
Transfer, scout, akademi, rakip, kulüp ve yönetim modülleri ortak ExpertDecision
sözleşmesine dönüştürülür.

## Ortak bağlam
Karar türü, konu kimliği, payload ve reliability tek FootballDecisionContext
nesnesinde taşınır.

## Builder
Adapterlar ağırlıklarıyla birlikte merkezi registry'ye eklenir. Consensus ve
risk politikası tek noktadan yapılandırılır.

## İzlenebilirlik
Her adapter kararı kategori, güven, risk ve gerekçeyle birlikte audit kaydına
aktarılır.

## Üretim sınırı
Bu sürüm adapter sözleşmelerini bağlar. Gerçek Sportmonks payload dönüşümleri,
database transaction sınırları ve dağıtık execution ayrıca sertleştirilmelidir.
