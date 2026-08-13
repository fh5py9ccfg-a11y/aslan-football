# v12.5 Deployment Safety Controller & Production Freeze

## Freeze windows

Tenant bazında başlangıç/bitiş zamanı, neden ve emergency bypass davranışıyla
production freeze pencereleri tanımlanır.

## Approval chain

Release için rol bazlı APPROVED veya REJECTED kararları aktör ve açıklamayla
saklanır.

## Risk score

Reliability score, SLO ihlalleri, progressive rollout durumu, verification
sonucu, değişiklik büyüklüğü ve etkilenen servis sayısı tek risk skoruna
dönüştürülür.

## Safety gate

Aktif freeze, eksik approval, reddedilmiş approval veya yüksek risk deployment'ı
durdurur.

## Emergency and override

Freeze politikası izin veriyorsa emergency release freeze'i aşabilir. Yetkili
operatör ayrıntılı nedenle bütün safety gate kararını override edebilir.

## Timeline

Approval, risk ve safety kararları release bazında birleşik zaman çizelgesinde
sunulur.
