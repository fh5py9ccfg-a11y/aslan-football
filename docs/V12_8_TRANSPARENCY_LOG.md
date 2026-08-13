# v12.8 Evidence Transparency Log

## Transparency entries

Doğrulanmış compliance attestation ve release evidence kayıtları append-only
transparency entry olarak yayımlanır.

## Merkle root

Tenant içindeki entry leaf hash'leri deterministic Merkle ağacında birleştirilir.
Tek sayıda leaf olduğunda son leaf kopyalanarak üst seviye hesaplanır.

## Checkpoints

Her checkpoint tree size, Merkle root ve önceki checkpoint hash'ini içerir.
Böylece checkpoint geçmişi ayrıca hash-chain ile korunur.

## Inclusion proof

Her entry için root hash'e ulaşan audit path üretilebilir ve dış istemciler
tarafından bağımsız olarak doğrulanabilir.

## Public verification

Latest checkpoint, inclusion proof ve checkpoint-chain verification endpoint'leri
kimlik doğrulaması gerektirmeyen public doğrulama yüzeyi sağlar.
