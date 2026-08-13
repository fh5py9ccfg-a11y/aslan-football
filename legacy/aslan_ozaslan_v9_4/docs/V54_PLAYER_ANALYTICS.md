# v5.4 Oyuncu Analitik Motoru

## Oyuncu alan modeli
Oyuncu ve maç bazlı performans kayıtları ayrı domain nesneleri olarak tanımlanır.

## Pozisyona göre normalizasyon
Bir oyuncu yalnızca ham sayılarla değil, kendi pozisyon grubunun ortalama ve
standart sapmasına göre değerlendirilir.

## Oyuncu değer skoru
Aşağıdaki boyutlar ayrı hesaplanır:
- hücum,
- yaratıcılık,
- topu ilerletme,
- savunma,
- pres,
- güvenilirlik.

## Form trendi
Yakın dönem performansı önceki dönemle karşılaştırılır ve RISING, STABLE veya
FALLING olarak sınıflandırılır.

## Kadro etkisi
Eksik oyuncuların beklenen dakika payı ve değer skorları üzerinden takımın
kullanılabilir kalite oranı hesaplanır.

## Üretim sınırı
Katsayılar ilk ürün sözleşmesidir. Gerçek pozisyon kümeleri, lig kalibrasyonu,
oyuncu rolü ve veri sağlayıcı farklılıklarıyla doğrulanmadan scouting veya
kadro kararı için tek başına kullanılmamalıdır.
