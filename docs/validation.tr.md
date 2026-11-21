# Doğrulama: yayımlanmış sayıların yeniden üretilmesi

İngilizce sürüm: [validation.md](validation.md). Her madde `tests/` altında otomatik bir testle tekrar ediliyor (`python -m pytest tests`).

## 1. Burgers vektörü popülasyonu (h kesirleri) ve b²C̄

### 1.1 Dragomir & Ungár 2002, J. Appl. Cryst. 35, 556, Bölüm 5.3 (yöntemin asıl kaynağı)
ECAP Ti için q₁ = −0,05 ± 0,02 ve q₂ = 0,18 ± 0,02 ölçülmüş. Makalenin sonucu: ⟨a⟩ %75 ± 10, ⟨c⟩ %20 ± 5, ⟨c+a⟩ %5 ± 3; b²C̄ = 0,0222 nm².

| Bizim hesap (tip ortalaması, Denk. 10–13) | h_a | h_c | h_c+a | b²C̄ (nm²) |
|---|---|---|---|---|
| Adım (i): S3 hariç tüm alt-sistemler | 0,763 | 0,224 | 0,013 | 0,0198 |
| Adım (iii): prizmatik ⟨a⟩ çift ağırlıklı | 0,725 | 0,226 | 0,049 | **0,0220** |
| Makale | 0,75 ± 0,10 | 0,20 ± 0,05 | 0,05 ± 0,03 | **0,0222** |

**Sonuç: yeniden üretildi.** h kesirleri her iki adımda da makalenin hata payı içinde. b²C̄ adım (iii) ile 0,0220'ye karşı 0,0222 çıkıyor. Adım (i) ile b²C̄ %11 düşük, bu da ρ'yu %11 yüksek verir. Bu fark yöntemin kendi belirsizliğidir ve raporda b²C̄ aralığı olarak gösteriliyor.

### 1.2 Muiruri, Maringa & du Preez 2020, Materials 13, 5355
- **b²C̄ (Tablo 4):** Makaledeki h değerlerinden tip ortalamasıyla hesaplanan b²C̄ değerlerinin beşi de makaleyle 4 basamak tutuyor (0,0253 / 0,0245 / 0,0245 / 0,0252 / 0,0249). **Yeniden üretildi.**
- **h (Tablo 4) ← q (Tablo 2):** **Yeniden üretilemiyor.** Makaledeki h değerleri, makalenin kendi q değerlerini vermiyor. Örneğin A numunesinde h = 0,88/0/0,12 geri hesaplanınca q₁ ≈ −0,14 çıkıyor, Tablo 2'de ise −0,34 yazıyor. Denenen tüm ortalama türleri (C-ağırlıklı, düz ortalama, b², b, b⁰ ağırlıkları, yalnız q₁ ya da yalnız q₂) ve 40 kombinasyon yöntemi farklı sonuç veriyor. Ayrıca q₁'i aynı olan B ve D numunelerinin h değerleri ters yönde değişiyor. Bu, makalenin iç tutarsızlığı. Muiruri'nin h değerleri referans alınmamalı.
- **A(L) formülü (Denk. 13):** Voigt profilinin Fourier dönüşümü değil (whitepaper, Bölüm 8). Bu yüzden Muiruri'nin ρ değerleri (Tablo 5) ham veri olmadan doğrudan karşılaştırılamaz.

### 1.3 Kombinasyon yöntemi (Burgers tipi başına bir alt-sistem)
`autodisloc.contrast.combinations()`, Dragomir & Ungár 2002 Denk. 11–13'ü bir ⟨a⟩, bir ⟨c⟩ ve bir ⟨c+a⟩ alt-sisteminin her kombinasyonu için çözer (Ti için 4 × 2 × 5 = 40); yani alt-sistemler her Burgers tipinden birine indirgenir (Dragomir 2002 §3.1). Test, her çözümün üç denklemi sağladığını (Σh = 1 ve ölçülen q₁, q₂'nin geri üretilmesi) denetler. Program **fiziksel çözümlerin (tüm h'ler 0–1 arasında) ortalamasını** verir.

Yöntemin tek koşulu, ölçülen q'nun Ti kayma sistemlerinin ulaşabildiği bölgenin içinde olmasıdır. Dışında kalırsa hiçbir kombinasyon fiziksel olmaz ve q'su bölgenin dışında kalan serbest bir uydurma ancak en yakın fiziksel noktayla (ör. saf ⟨a⟩ köşesi) temsil edilebilir.

**Kısıtlı mWH.** Kontrast faktörü doğrudan h kesirleriyle yazılıyor:

ΔK² = α + K² Σ g_t P_t (1 + q₁ᵗ x + q₂ᵗ x²), g_t ≥ 0

Bu yazımda q her zaman fiziksel ve h her zaman kesirli. q zaten bölgenin içindeyse sonuç serbest uydurmayla aynı (test edildi).

## 2. Modifiye Williamson–Hall

### Shintani, Murata ve ark. 2010, Mater. Trans. 51, 1067 (Mg AX52, hcp; FWHM tablosu verilmiş)
Tablo 3'teki 6 pik genişliğinden makaledeki α = 4,29×10⁻⁵ nm⁻² ve D = 137 nm, ancak **ΔK = 2cosθ·FWHM(2θ)/λ** kullanılırsa çıkıyor (bizde 4,44×10⁻⁵ ve 135 nm). Doğru tanımla α dört kat küçük çıkıyor; q değişmiyor. **mWH kodumuz, yazarların kendi tanımı verildiğinde makalenin sayısını üretiyor.**

## 3. Tam profil (Wilkens) uydurması: CMWP tipi ana sonuç

- **Sentetik geri kazanım:** Bilinen ρ, M*, h ve boyut dağılımıyla, korundum cihaz modeli ve Poisson gürültüsü eklenerek Ti-6Al-4V deseni üretildi. ρ %2–18 içinde (en büyük sapma en zayıf genişlemede), h_a 0,01–0,02 içinde geri bulundu; χ²/ν ≈ 1 (whitepaper, doğrulama bölümü; `tests/test_wholeprofile.py`).
- **Literatür karşılaştırma değeri:** Cottam ve ark. 2019, Metals 9, 60, SLM Ti-6Al-4V, eCMWP (nötron): ρ = (2,4 ± 0,3)×10¹⁵ m⁻², ⟨a⟩ %85, ⟨c+a⟩ %10, ⟨c⟩ %5. 
- **Asıl doğrulama hâlâ açık:** Aynı ham verinin CMWP (Ribárik) ile analiz edilip karşılaştırılması. Kendi kodumuz CMWP'nin modelini (Wilkens + log-normal boyut + Dragomir kontrastı) kullanıyor, ama programın kendisiyle karşılaştırılmadı.

## 4. Kontrast sabitleri tablosu
`TI_SUBSYSTEMS`, Dragomir & Ungár 2002 Tablo 2'nin Ti sütunuyla tek tek karşılaştırıldı; 11 alt-sistemin tümü aynı. Muiruri Tablo 3 de aynı sayıları kullanıyor.
