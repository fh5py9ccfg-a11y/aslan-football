# Kimlik Eşleştirme ve Tarihsel Veri

Gerçek sağlayıcılar aynı takımı farklı kimliklerle tanımlar. Aslan Özaslan, ham sağlayıcı
kimliklerini doğrudan modelde kullanmaz. Her dış kimlik önce değişmez bir kanonik takım
kimliğine bağlanır. Çakışan eşleşmeler otomatik olarak reddedilir ve elle incelenir.

Tarihsel veriler üzerine yazılmaz; zaman damgalı snapshot olarak saklanır. Böylece geçmişte
üretilen bir tahminin o gün hangi veriye dayandığı yeniden oluşturulabilir.

## Temel kurallar
- Sağlayıcı kimliği eşleşmeden model çalışmaz.
- Aynı dış kimlik iki farklı kanonik takıma bağlanamaz.
- Ham snapshot kayıtları geriye dönük değiştirilmez.
- Fikstür ve takım organizasyonu aynı değilse tahmin engellenir.
- Güncellik eşiğini aşan veri model girdisi olamaz.
