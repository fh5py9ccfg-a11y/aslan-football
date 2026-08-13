# v4.0 Operasyon Kontrol Merkezi, Onay ve Kurtarma

## Bakım zamanlaması
Audit zinciri, sertifika kontrolleri ve diğer bakım görevleri tek bakım çalışması
altında yürütülebilir. Kritik görev başarısızlığı sistem sağlığını bozar.

## Secret rotation kurtarma
Yeni secret sürümü sorun çıkarırsa başarısız sürüm devre dışı bırakılır.
Eski sürüm daha önce emekliye ayrılmışsa yeniden aktifleştirilebilir.

## Release approval
Production release için birbirinden farklı en az iki approver gereklidir.
Aynı kişinin tekrarlanan onayı onay sayısını artırmaz.

## Operasyon kontrol merkezi
Sağlık, audit zinciri, sertifika alarmları, dead-letter işleri, drift alarmları,
release onayı, policy sonucu ve imzalı bundle doğrulaması tek snapshot içinde
birleştirilir.

## Release kararı
Sağlık, audit, onay, policy ve imza kontrollerinden biri başarısızsa veya
sertifika/dead-letter alarmı varsa release hazır sayılmaz.
