# v10.23 Lossless Maintenance Resume

## Pending batch checkpoint
Redis SCAN bir anahtar batch'i döndürdüğünde batch'in tamamı progress kaydına
yazılır. Her indeks işlendiğinde pending listeden çıkarılıp tekrar checkpoint
alınır.

## Atlanmayan indeksler
Zaman bütçesi, batch sınırı, lease kaybı veya process restart batch ortasında
gerçekleşse bile kalan anahtarlar sonraki turda önce işlenir. SCAN cursor yalnızca
pending batch tüketildikten sonra ilerletilir.

## Kümülatif ilerleme
Progress kaydı toplam işlenen indeks sayısını, tamamlanan cycle sayısını, aktif
fazı, cursor'u ve bekleyen anahtar sayısını içerir.

## Güvenli reset
Admin, aktif fencing token ile bakım progress kaydını kontrollü biçimde
sıfırlayabilir.

## Üretim sınırı
Çok büyük SCAN count değerleri progress kaydını büyütür. Varsayılan 100 anahtarlık
batch, Redis payload boyutu ile throughput arasında dengelidir.
