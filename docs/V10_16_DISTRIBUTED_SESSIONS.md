# v10.16 Distributed Refresh Sessions

## Redis session store
Refresh oturumları üretimde Redis üzerinde tutulur. Oturum; subject, roller,
family ID, rotation sayısı, cihaz bilgisi, IP ve son kullanım zamanını içerir.

## Reuse detection
Daha önce kullanılmış refresh secret yeniden sunulursa token reuse olarak kabul
edilir ve ilgili token ailesi iptal edilir.

## Session management
Kullanıcı kendi oturumlarını listeleyebilir, tek oturumu iptal edebilir veya tüm
cihazlardan çıkış yapabilir.

## Üretim sınırı
Redis family iptal işlemi mevcut uygulamada session key'lerini SCAN ile bulur.
Çok yüksek oturum hacminde family → session indeks seti kullanılmalıdır.
