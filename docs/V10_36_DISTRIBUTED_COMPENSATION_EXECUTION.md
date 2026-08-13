# v10.36 Distributed Compensation Execution

## Tekil execution claim
Her compensation kaydı çalıştırılmadan önce Redis execution lease alınır. Aynı
kayıt farklı worker'lar tarafından eşzamanlı çalıştırılamaz.

## Lease ve takeover
Aktif execution lease süresi dolmadan başka worker devralamaz. Worker çökerse
lease süresi sonunda yeni owner token ile güvenli takeover yapılabilir.

## Stale owner koruması
Takeover sonrasında eski owner token ile complete çağrısı Redis tarafından
reddedilir.

## Restart idempotency
COMPLETED execution kaydı saklandığı için process restart sonrasında aynı
compensation handler tekrar çalıştırılmaz.

## Üretim sınırı
Uzun compensation handler'ları için heartbeat guard sınıfı hazırdır; gerçek dış
sistem handler'ları bağlandığında orchestration boyunca otomatik heartbeat
başlatılmalıdır.
