# Build 024 — Supply Chain Security

## SBOM

Python ortamındaki bağımlılıklar isim, sürüm, kaynak, lisans ve checksum ile
`SBOM.json` dosyasına yazılır.

```bash
python scripts/generate_sbom.py
```

## Lisans denetimi

Durumlar:

- PASS: Bilinen ve izin verilen lisanslar
- REVIEW: Bilinmeyen lisanslar
- BLOCKED: Yasak lisans tespit edildi

## Paket bütünlüğü

```bash
python scripts/verify_package_integrity.py package.zip EXPECTED_SHA256
```

## Tekrarlanabilir build

```bash
python scripts/reproducible_build_check.py
```

Aynı kaynak ağacından üretilen iki manifest checksum'ı eşleşmelidir.
