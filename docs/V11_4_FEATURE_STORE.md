# v11.4 Feature Store v2 & Online Feature Serving

## Feature definitions

Feature adı, sürümü, entity tipi, veri tipi, TTL, freshness sınırı, kaynak,
dönüşüm ve sahiplik bilgisi kayıt altına alınır.

## Online store

En güncel feature değeri tenant ve entity bazında Redis üzerinde düşük gecikmeli
olarak sunulur.

## Offline store

Tarihsel feature değerleri sorted-set zaman çizgisinde tutulur.

## Point-in-time correctness

`as_of` sorgusu yalnızca belirtilen zamandan önce üretilmiş son feature değerini
döndürür.

## Freshness

Feature yaşı ile tanımlı maksimum yaş karşılaştırılır.

## Lineage

Kaynak, dönüşüm, sahip, durum ve entity bilgileri tek lineage görünümünde
sunulur.
