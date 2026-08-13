# v10.27 Quarantine Diagnostics & Safe Retry

Karantinadaki indeks için dry-run tanılama; indeks varlığı, TTL, canlı session ve
orphan session sayılarını hesaplar. Sonuç RELEASE, RETRY veya HOLD önerisi üretir.

Operatör retry endpoint'i yalnızca ilgili indeks üzerinde tek bakım işlemi
çalıştırır. Sonuç başarılı olsa bile karantina kaydı otomatik kapatılmaz; release
ayrı operatör onayı gerektirir.
