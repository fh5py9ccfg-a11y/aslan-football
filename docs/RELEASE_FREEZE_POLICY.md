# Release Freeze Policy

Bu sürümden sonra:

- Yeni özellik kabul edilmez.
- Schema değişikliği migration preflight olmadan yapılmaz.
- Kritik güvenlik düzeltmeleri dışında deploy yapılmaz.
- Her teslim imzalı release manifesti içermelidir.
- Production preflight PASS olmadan yayın yapılmaz.
- Felaket kurtarma provası FAIL ise yayın engellenir.
