# Supply Chain Policy

- Her final paket SBOM içermelidir.
- Bilinmeyen lisanslar manuel inceleme olmadan production'a çıkamaz.
- Yasak lisans içeren bağımlılıklar release'i engeller.
- Paket checksum yayın notuna eklenir.
- Teslim manifesti ve paket checksum ayrı ayrı doğrulanır.
- Build manifesti deterministik olmalıdır.
- Bağımlılık sürümleri release sonrasında değiştirilmez.
