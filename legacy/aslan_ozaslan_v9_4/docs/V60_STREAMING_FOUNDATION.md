# v6.0 Streaming Foundation

## Sıralama
Provider eventleri sequence numarasıyla işlenir. Sırası bozuk gelen eventler,
eksik sequence tamamlanana kadar buffer'da tutulur.

## Checkpoint
Her başarılı batch sonrasında stream checkpoint atomik JSON yazımıyla kalıcı hale
getirilir.

## Correction
Bir event sonradan değiştirilebilir veya pasif hale getirilebilir. Ledger her
değişiklikte event versiyonunu yükseltir.

## Recovery
Provider high watermark ile yerel checkpoint karşılaştırılarak hangi sequence'den
replay başlanacağı belirlenir.

## Üretim sınırı
Bu sürüm Kafka/NATS istemcisi değildir. Consumer group, partition rebalancing,
distributed lock, exactly-once sink ve harici veritabanı henüz bağlı değildir.
