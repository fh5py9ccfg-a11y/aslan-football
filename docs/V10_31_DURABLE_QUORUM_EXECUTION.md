# v10.31 Durable Quorum Execution

## Kalıcı execution claim
Quorum tamamlandığında closure çalıştırılmadan önce Redis üzerinde tekil execution
claim oluşturulur. Aynı talebi başka process veya instance yeniden çalıştıramaz.

## Restart sonrası idempotency
Closure sonucu Redis'te COMPLETED olarak saklanır. API instance yeniden başlasa
bile daha önce tamamlanmış işlem tekrar yürütülmez.

## Rol bağlama
Oy veren kişinin bildirdiği voter group, access token içindeki doğrulanmış roller
arasında bulunmak zorundadır.

## Risk tabanlı politika
Orphan sayısı, canlı session etkisi, TTL durumu, retry sayısı ve indeks fazına göre
LOW, MEDIUM, HIGH veya CRITICAL risk politikası üretilir.

## Üretim sınırı
IN_PROGRESS execution owner'ı çökerse kayıt TTL dolana kadar yeni execution
başlatılmaz. Sonraki adım owner heartbeat ve kontrollü takeover'dır.
