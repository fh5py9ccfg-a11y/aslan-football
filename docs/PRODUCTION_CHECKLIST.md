# Production Checklist

- [ ] `MVP_AUTH_SECRET` en az 32 karakter ve benzersiz
- [ ] Demo kullanıcı parolaları kaldırıldı veya değiştirildi
- [ ] HTTPS aktif
- [ ] Redis dış erişime kapalı
- [ ] Veritabanı yedekleme planı aktif
- [ ] Backup restore doğrulaması çalıştırıldı
- [ ] Smoke test geçti
- [ ] Load probe p95 hedefi geçti
- [ ] Release gate sonucu GO
- [ ] Pilot readiness sonucu READY
- [ ] Audit log saklama politikası tanımlandı
- [ ] İzleme ve alarm kanalları aktif
