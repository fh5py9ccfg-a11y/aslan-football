# v12.1 Reliability Score & Error Budget Management

## SLO registry

Tenant ve servis bazında service level objective tanımlanır. Her SLO hedef oran,
ölçüm penceresi ve warning/critical burn-rate eşiklerini taşır.

## Observations

Başarılı ve toplam olay sayıları zaman damgalı observation kayıtları olarak
saklanır.

## Error budget

Seçilen pencere içindeki başarısız olaylar, SLO'nun izin verdiği hata bütçesiyle
karşılaştırılır. Kalan bütçe, tüketim yüzdesi ve burn rate hesaplanır.

## Reliability score

Tenant içindeki etkin SLO'ların kalan hata bütçeleri tek bir reliability score
altında özetlenir.

## Operasyon

SLO oluşturma, observation kaydı, error-budget sorgusu ve tenant reliability
score endpoint'leri sağlanır.
