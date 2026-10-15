# Paket işlemi sonucunun doğrulanması

16 Ekim 2026, Pardus 25.2 / XFCE, Python 3.13. Temel: resmî
`pardus-package-installer 0.7.0`, upstream
`3508fbb6f1aa52f8d715a29766c9f4f930cfefe1`. Düzeltme:
[`bf830ad`](https://github.com/muhammetali/pardus-package-installer/commit/bf830ad1e15b7a0b977a64274748097c9305c943).
Bu dal yalnız deney kayıtlarını içerir.

## Doğrulanan hata

Küçük bir yerel test paketinin `prerm` betiği kaldırma sırasında 42 ile çıkıyor.
APT işlemi başarısız oluyor ve paket kurulu kalıyor. Özgün yardımcı program
APT'nin dönüş değerini iletmediği için 0 ile çıkıyor; arayüz başarı sayfasına
geçip başarı bildirimini etkinleştiriyor. Düzeltmeden sonra yardımcı 100 ile
çıkıyor; arayüz **Tamamlanamadı** gösteriyor, başarı bildirimi üretmiyor.

| Gerçek arayüz işlemi | Özgün paket | Düzeltme |
| --- | --- | --- |
| Yerel 1.0 kurulumu | Başarı; 1.0 kurulu | Başarı; 1.0 kurulu |
| `prerm` nedeniyle başarısız kaldırma | Yanlış başarı; 1.0 kurulu | Hata; 1.0 kurulu |
| 1.0 yeniden kurulum | Ölçülmedi | Başarı; 1.0 kurulu |
| 1.0 → 2.0 yükseltme | Ölçülmedi | Başarı; 2.0 kurulu |
| 2.0 → 1.0 düşürme | Ölçülmedi | Başarı; 1.0 kurulu |
| Normal kaldırma | Ölçülmedi | Başarı; paket kaldırılmış |

[Önce](screenshots/before-failed-remove.png) ·
[Sonra](screenshots/after-failed-remove.png) ·
[Ham olaylar: önce](logs/before-events.json) / [sonra](logs/after-events.json).
Olaylardaki `wait_status`, GLib'in ham bekleme durumudur: 25600, çıkış kodu 100'dür.

Olmayan bir `.deb` ile yardımcı ayrıca doğrudan çalıştırıldı: özgün yardımcı 0,
aynı APT komutu 100; düzeltmeden sonra yardımcı da 100 döndü.
[Önce](logs/yardimci-once.log) / [sonra](logs/yardimci-sonra.log).

## Yöntem ve sınırlar

Önce VM anlık görüntüsü alındı. [Paket üreticisi](scripts/package-installer-fixtures.py)
yalnız bir işaret dosyası içeren, bağımlılığı olmayan test paketleri oluşturur.
`warning.deb` kaldırmayı reddeder; `cleanup.deb` aynı sürümü bu betik olmadan
yeniden kurar; `upgrade.deb` 2.0 sürümüdür. Temizlemek için `cleanup.deb` yeniden
kurulup `pardus-install-result-test` kaldırılır. Kendi paket verileri dışında
dosyalara veya dpkg veritabanına elle müdahale edilmez.

[Deney sürücüsü](scripts/package-installer-live.py), kurulu uygulamanın gerçek
GTK başlangıcını ve düğme sinyallerini kullanır. Önbellek, APT, pkexec ve yardımcı
program taklit edilmez. Açık masaüstü oturumunu korumak için arayüz Xvfb'de
çalıştırılır. Ekran görüntüleri gerçek GTK penceresinden alınır; hata mesajı veya
çıktı görüntüye sonradan eklenmez. Sonra görüntüsü Detaylar/çıktı sekmesini de
gösterir. Laboratuvarda yalnız bu polkit eylemi ve test kullanıcısı için
geçici izin kuralı kullanılmıştır; normal elle tekrarda standart yetki diyaloğu
kullanılabilir.

Deney sonunda özgün 0.7.0 paketi geri kuruldu, test paketi ve geçici polkit kuralı
kaldırıldı. `dpkg --audit` ve paket dosya doğrulaması temiz; bozuk bağımlılık 0.
[Son durum](logs/son-durum.log).

`install_warning` deney adıdır: 0700 dizindeki yerel paket bu Pardus 25
ortamında `_apt` erişim uyarısı üretmedi. Bu koşu başarılı kurulum kontrolüdür;
gerçek APT uyarısıyla yanlış hata üretildiği iddia edilmiyor. `.deb` içeren
uyarıların yanlış hata sayılması ayrı GTK regresyon testinde gösterildi.
Harici test paketi kurulduktan sonra sürüm karşılaştırması 2 (`VERSION_SAME`)
döndü; depoda bulunmaması tek başına 0 sonucu doğurmadı.

Bu çalışma #6'daki işlem sonucu değerlendirmesini ele alır. İlk temiz kurulumun
boş depo listesi senaryosu veya eski bildirimin özgün ortamı yeniden üretilmedi.
Pardus 23 üzerinde bu değişiklik denenmedi.

## Regresyon ve derleme

Kaynak dalında normal kullanıcıyla:

```sh
python3 tests/actions.py
xvfb-run -a python3 tests/operation_result.py
```

4 yardımcı + 10 GTK testi düzeltmeden sonra geçti. Aynı testlerin özgün kaynak
üzerindeki 6 test metodu hata yakaladı; 8 kontrol metodu geçti. Eksik argüman
testindeki `IndexError` özgün yardımcı programdan gelir. Testler APT/yetki
işlemlerini taklit eder; çıktı testleri gerçek, zararsız Python alt süreçleri
çalıştırır. 300'er çıktı satırı ve son tanı satırı tamamlanma anından önce
korunur; boruların çocuk süreçten önce kapanması ve art arda işlemler de sınanır.

[Regresyon önce](logs/regresyon-once.log) / [sonra](logs/regresyon-sonra.log).
`dpkg-buildpackage -us -uc -b` ile `0.7.0+result1` test paketi derlendi ve VM'de
kuruldu; kurulu iki kaynak dosyasının SHA-256 değerleri yama ile aynı.
[Derleme kaydı](logs/paket-derleme.log). Pybuild otomatik keşfi test çalıştırmıyor;
yukarıdaki 14 test ayrıca çalıştırıldı. Yerel sürüm eki kaynak PR'ına eklenmedi.
