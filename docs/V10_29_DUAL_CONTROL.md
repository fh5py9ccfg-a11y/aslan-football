# v10.29 Dual-Control Quarantine Closure

## Maker-checker
Karantina kapatma talebini oluşturan kullanıcı aynı talebi onaylayamaz. Kapatma
yalnızca ayrı bir admin onayından sonra çalışır.

## Approval expiry
Onay talepleri sınırlı süre geçerlidir. Süresi geçen talep yürütülemez.

## Idempotent decision
Daha önce karar verilmiş talebe tekrar karar verilirse mevcut karar döndürülür;
kapatma ikinci kez tetiklenmez.

## Tamper-evident audit
Her talep ve karar HMAC tabanlı record hash ve previous hash ile zincirlenir.
Operatörler claim bazında zincir bütünlüğünü kontrol edebilir.

## Üretim sınırı
Bu sürüm tek admin onayı gerektirir. Yüksek riskli ortamlarda iki veya daha fazla
checker quorum desteği eklenebilir.
