# Uçtan Uca Analiz Hattı

Akış sırası:

1. Maç ve takım kimliği doğrulama
2. Lig parametresi kontrolü
3. Veri güncelliği ve kalite kapısı
4. Kadro/sakatlık etkisi
5. Hücum-savunma-form-Elo birleşimi
6. Beklenen gol hesabı
7. Poisson skor ve 1-X-2 dağılımı
8. Piyasa oranlarıyla karşılaştırma
9. Güven puanı
10. Açıklama ve sınırlamalar
11. Hesaplama kimliği ve sürüm kaydı

## Bloklama

Aşağıdaki durumlarda yüzde gösterilmez:
- ertelenmiş maç,
- eski veri,
- düşük veri kalitesi,
- pasif lig,
- aynı takım kimliği,
- kritik bileşen hatası.

## Şüpheli tekrar

Üç farklı maçta aynı tam olasılık dağılımı görülürse alarm üretilir ve canlı
tahmin hattı inceleme tamamlanana kadar durdurulmalıdır.
