# v12.9 Transparency Witness & Consistency Proofs

## Witness registry

Tenant bazında bağımsız witness kimlikleri ve anahtar kimlikleri tanımlanır.
Witness secret yalnızca imza doğrulamasında kullanılır.

## Checkpoint signatures

Her witness checkpoint hash'ini HMAC-SHA256 ile imzalar. İmzalar checkpoint,
witness ve key ID ile birlikte saklanır.

## Quorum

Public quorum endpoint'i geçerli ve geçersiz witness imzalarını ayırır ve
istenen minimum witness sayısının karşılanıp karşılanmadığını bildirir.

## Consistency proofs

İki checkpoint arasındaki eklenen leaf hash'leri kanıt paketine alınır. Source
ve target root hash'leri mevcut transparency entry setinden yeniden hesaplanır.

## Fork detection

Checkpoint root hash'i yeniden hesaplanan root ile uyuşmazsa checkpoint stale
veya fork edilmiş kabul edilir.

## Public verification

Consistency proof hash'i, root'lar ve appended leaf seti dış istemciler
tarafından bağımsız olarak doğrulanabilir.
