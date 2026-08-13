# v10.32 Quorum Execution Heartbeat & Takeover

## Execution lease
Her IN_PROGRESS closure execution kaydı kısa süreli owner lease'i taşır.

## Heartbeat
Aktif owner lease süresini düzenli heartbeat ile yenileyebilir.

## Kontrollü takeover
Owner çöker ve lease süresi dolarsa yeni worker aynı request için yeni owner token
ve artırılmış attempt sayısıyla execution kaydını devralabilir.

## Stale owner koruması
Takeover sonrasında eski owner token ile complete çağrısı reddedilir.

## Operasyonel görünürlük
Admin ve ops kullanıcıları request bazında execution owner, heartbeat, lease
bitişi, attempt ve sonuç durumunu görebilir.

## Üretim sınırı
Heartbeat sınıfı hazırdır; closure uzun süren dış çağrılar içermeye başladığında
servis katmanında execution boyunca otomatik başlatılmalıdır.
