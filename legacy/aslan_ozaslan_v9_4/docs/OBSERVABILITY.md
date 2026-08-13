# İzlenebilirlik ve Alarm

Ölçülecek temel değerler:
- Veri sağlayıcı erişilebilirliği
- Son başarılı veri çekme zamanı
- Eksik veri oranı
- Tahmin üretilmeyen maç oranı
- Aynı olasılık dağılımının tekrar sıklığı
- API hata oranı
- Cache çakışma sayısı
- Model sürümüne göre kalibrasyon

Kritik alarm:
Üç farklı maçta aynı tam olasılık dağılımı oluşursa canlı sistem otomatik olarak
tahmin üretimini durdurur ve inceleme ister.
