# AutoDisloc 2

**X-ışını çizgi profili analiziyle hcp α/α′ titanyum alaşımlarında (Ti-6Al-4V, CP-Ti, …) dislokasyon yoğunluğu**

[English](README.md) · [Kullanım kılavuzu (PDF)](docs/manual/AutoDisloc2_Manual_TR.pdf) · [Whitepaper (PDF)](docs/whitepaper/AutoDisloc2_Whitepaper_TR.pdf) · [Doğrulama](docs/validation.tr.md) · Lisans: MIT

AutoDisloc laboratuvar XRD desenlerinden dislokasyon yoğunluğunu (ρ), Burgers vektörü popülasyonunu (⟨a⟩, ⟨c⟩ ve ⟨c+a⟩ dislokasyonlarının oranları) ve Wilkens düzen parametresini (M*) hesaplar. Üç yerleşik çizgi profili yöntemini birleştirir:

| Adım | Yöntem | Görevi |
|---|---|---|
| 1 | Voigt pik uydurma (Kα1 + Kα2 ikilisi), çizgi standardından cihaz modeli | pik genişlikleri, kafes parametreleri |
| 2 | Dragomir–Ungár hekzagonal kontrast faktörleriyle modifiye Williamson–Hall (mWH); fiziksel olarak ulaşılabilir Burgers popülasyonlarıyla kısıtlı | kontrast faktörleri, Burgers vektörü popülasyonu |
| 3 | **Wilkens tam profil uydurması** (CMWP tipi): boyut (log-normal küreler) × dislokasyon (Wilkens) × cihaz Fourier katsayıları ölçülen profillere doğrudan uydurulur | **ana sonuç: %95 aralığıyla ρ, M*, h, boyut** |
| – | Voigt tabanlı modifiye Warren–Averbach (mWA) | karşılaştırma için raporlanır |

Matematik, bilinen mikroyapılı sentetik bir Ti-6Al-4V deseni üzerinde [whitepaper](docs/whitepaper/AutoDisloc2_Whitepaper_TR.pdf)'da adım adım türetilir.

## Masaüstü programı (macOS ve Windows)

[Kullanım kılavuzu](docs/manual/AutoDisloc2_Manual_TR.pdf) kurulumu, pencerenin her öğesini ve tüm çıktıları ekran görüntüleriyle adım adım anlatır. Programdaki *Kullanım kılavuzu* düğmesiyle de açılır.

Arayüz Türkçe ve İngilizcedir (araç çubuğundaki **TR | EN** düğmeleri).

| | macOS | Windows |
|---|---|---|
| Hazır uygulama | Releases sayfasından `AutoDisloc2_macOS.zip`'i (Apple Silicon) indirip açın. Uygulama Apple tarafından imzalı değildir: bir kez açmayı deneyin, sonra *Sistem Ayarları › Gizlilik ve Güvenlik › Yine de Aç* (macOS 14 ve öncesi: sağ tık › **Aç**). Intel Mac'lerde kaynaktan çalıştırın. | Releases sayfasından `AutoDisloc2_Windows.zip`'i indirip açın; SmartScreen uyarırsa *Ek bilgi › Yine de çalıştır*. Ya da `packaging\build_windows.bat` ile derleyin |
| Kaynaktan çalıştırma | `AutoDisloc2_Mac.command` çift tıklama | `AutoDisloc2_Windows.bat` çift tıklama |

Kaynaktan çalıştırmak için: Python ≥ 3.9 ve `pip install -r requirements.txt`.

Kullanım (isteğe bağlı olarak her girdiyi sırayla soran ve analiz başlatılırken önerilen **Adım adım sihirbaz** ile):
1. **Cihaz modeli.** Örnek bir model (programın geliştirildiği difraktometrenin korundum standardı) yüklenir. Aynı yarıklarla ölçülmüş bir çizgi standardından kendi modelinizi oluşturun: *Standart desenden oluştur…*; standart malzemeyi (LaB6 SRM 660c, Si SRM 640f, CeO2, korundum ya da *diğer*) ve sertifikalıysa kafes parametresini seçin. Pikler indekslenir, standarda ait olmayan çizgiler atılır ve gonyometre sıfır kayması belirlenir.
2. **Numuneler.** *Ekle…* ile desenleri seçin: Bruker RAW v1.01 (`.raw`), Bruker UXD (`.uxd`), PANalytical XRDML (`.xrdml`) ya da iki sütunlu `.xy/.dat/.txt/.csv`. Adı değiştirmek için çift tıklayın; ad grafiklerde ve tablolarda kullanılır.
3. **Ölçüm ve malzeme.** Dalga boyları, Kα2/Kα1 oranı ve gonyometre yarıçapı dosyalardan okunur; dosyada olmayan *varsayıldı* olarak gösterilir ve elle girilebilir (Cu, Co, Fe, Cr, Mo, Ag Kα ya da özel; iki sütunlu dosyalara `# WL1 = …` başlık satırları eklenebilir, bkz. `examples/README.md`). Ham (Kα2 ayıklanmamış) veri önerilir: her pik Kα1 + Kα2 ikilisi olarak modellenir. Hazır alaşımlar: Ti-6Al-4V (α/α′ + β), CP-Ti (α) ya da özel kafes parametreleri; kontrast faktörleri α-Ti'ye aittir.
4. **Analizi başlat.** Sekmeler: Özet (karşılaştırma grafiği ve tablo), Desen, Tam profil, mWH, mWA, Burgers vektörü, Fourier bileşenleri, Cihaz, Uyarılar, Pik tablosu.
5. **Dışa aktarma.** *Bu grafiği kaydet…* (PNG/TIFF 600 dpi, PDF, SVG) ya da *Tümünü dışa aktar (makale paketi)…*: her grafik dört formatta, sütun açıklamaları sayfalı Excel raporu, sonuç tablosu CSV ve LaTeX olarak. Çıktı dosyalarının üst verisine yalnızca program adı ve sürümü (ör. "AutoDisloc 2.0.0") yazılır.

Grafikler dergi sütun genişliklerinde (8,5 cm ve 17,5 cm), renk körlüğüne uygun bir paletle çizilir.

## Komut satırı

```bash
python -m autodisloc --lang tr cihaz STANDART.raw -o cihaz.json
python -m autodisloc --lang tr analiz N1.raw N2.raw -c cihaz.json -o rapor.xlsx --paket makale_paketi
```

Seçenekler: `--ka2 auto|present|stripped`, `--radiation Cu|Co|Fe|Cr|Mo|Ag|WL1,WL2[,ORAN]`, `--radius MM`, `--standard corundum|LaB6|Si|CeO2|other` ve `--std-lattice A[,C]` (cihaz), `--material Ti-6Al-4V|CP-Ti`, `--lattice A,C[,Aβ]`, `--zero`, `--mwh constrained|free`, `--fourier voigt|eq13` (Voigt-mWA'nın A(L)'si: Voigt dönüşümü ya da karşılaştırma için Muiruri 2020 Denk. 13), `--mc N`, `--tam-profil-yok`. İngilizce komut adları (`instrument`, `analyze`) eşdeğerdir.

## Klasör yapısı

| Yol | İçerik |
|---|---|
| `autodisloc/` | hesap motoru, masaüstü programı (`gui.py`), grafikler, rapor, Türkçe/İngilizce metinler (`i18n.py`) |
| `autodisloc/data/` | örnek cihaz modeli |
| `docs/manual/` | Türkçe ve İngilizce kullanım kılavuzu (PDF/HTML), ekran görüntüleri ve üretim betikleri |
| `docs/whitepaper/` | Türkçe ve İngilizce whitepaper (PDF/HTML) ve onu motordan üreten betik |
| `docs/validation.tr.md` | yayımlanmış sayıların yeniden üretimi |
| `examples/` | bilinen mikroyapılı sentetik Ti-6Al-4V desenleri ve üreticisi |
| `tests/` | otomatik testler (`python -m pytest tests`) |
| `packaging/` | PyInstaller tanımı, macOS ve Windows derleme betikleri |

## Sınırlamalar

- Kontrast faktörü sabitleri saf Ti içindir (Dragomir & Ungár 2002).
- Ortalama kontrast faktörü dokusuz bir çok kristal varsayar; güçlü dokulu yansımalar işaretlenir (Harris doku katsayısı).
- Zayıf genişlemeli numunelerde ρ ile M* birlikte belirlenemez; M* sabitlenir ve aralık bir M* bandını kapsar (whitepaper, Bölüm 10). Varsayılan referans M* = 2.64 (bant 1.5–4.0), programın geliştirilmesi sırasında örnek cihaz modeliyle ölçülmüş iyi koşullu iki numunenin serbest uydurma M* değerlerinin (2.17 ve 3.21) geometrik ortalamasından ibarettir; evrensel bir sabit değildir. Bu durumda ρ varsayılan M*'a bağlıdır (büyük M* daha küçük ρ verir); referans M*'ı (*Referans M\** seçeneği) malzemenize ve cihazınıza uygun bir değere ayarlayın, ör. kendi iyi koşullu numunelerinizin serbest uydurmalarından.
- **M* tanımı.** Program Wilkens fonksiyonu f*(η)'yı η = L/Re* ile hesaplar; Re* = Re/(e^1.75/2) = Re/2.877, Re mWA denkleminin logaritmik ln(Re/L) biçimindeki kesme yarıçapıdır; raporlanan M* = Re*·√ρ'dur. Wilkens ve MWP-fit/CMWP η = ½·e^(−1/4)·L/Re* ve M* = Re*·√ρ kullanır ([Ribárik, Ungár & Gubicza 2001, J. Appl. Cryst. 34, 669, Denk. 4](https://doi.org/10.1107/S0021889801011451); Re = e²·Re*). Aynı fiziksel durum için **M\*(CMWP) = M\*(AutoDisloc) / (2·e^(1/4)) = M\*(AutoDisloc) / 2.568**'dir (Re* için de aynı çarpan). [Ungár vd. 2001, J. Appl. Cryst. 34, 298](https://doi.org/10.1107/S0021889801003715)'in düzen parametresi M = Re·√ρ (Denk. 25a, ln biçimindeki Re) 2.877 × M\*(AutoDisloc)'a eşittir. ρ tüm tanımlarda aynıdır.
- En küçük kareler ağırlıkları (1/√y) ve dolayısıyla χ²/dof ile hata aralıkları ham sayım varsayar. Saniye başına sayım, normalize edilmiş ya da başka biçimde işlenmiş şiddet içeren dosyalar aynı şekilde analiz edilir, ancak bir uyarı gösterilir; ham sayım verisi önerilir.
- Aynı veri üzerinde CMWP programıyla doğrudan karşılaştırma henüz yapılmadı.

## Lisans

AutoDisloc [MIT Lisansı](LICENSE) ile yayımlanmıştır. Hazır uygulamalar ayrıca üçüncü taraf bileşenler içerir (GNU LGPLv3 ile Qt/PySide6, NumPy, SciPy, pandas, matplotlib, openpyxl, Pillow, Python); bkz. [THIRD-PARTY-NOTICES.md](THIRD-PARTY-NOTICES.md). Lisans metinleri her paketin içindedir (*Hakkında › Üçüncü taraf lisansları*); Qt kaynak arşivleri her sürüme eklenir.

## Geliştirme

AutoDisloc'un hesaplama yöntemi, yazarın doktora tezindeki dislokasyon yoğunluğu ölçüm yöntemine dayanır (TOBB Ekonomi ve Teknoloji Üniversitesi, 2025). Python uygulaması, grafik kullanıcı arayüzü, raporlar, paketleme ve belgeler, yazarın yönlendirmesi ve denetiminde Claude Opus 5.5 (Anthropic) yardımıyla geliştirilmiştir.

## Atıf

AutoDisloc'u bilimsel çalışmalarda kullanırsanız [CITATION.cff](CITATION.cff)'teki künyeyle kaynak gösterin (GitHub: *Cite this repository*; her sürümde Zenodo DOI).

© 2026 Fırat Memu · MIT Lisansı
