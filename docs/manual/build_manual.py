# SPDX-License-Identifier: MIT
# AutoDisloc 2 - Copyright (c) 2026 Firat Memu
"""Build the AutoDisloc 2 user manual (Turkish and English, HTML + PDF).

    QT_QPA_PLATFORM=offscreen python docs/manual/make_screenshots.py   # screenshots
    python docs/manual/build_manual.py                                   # manual

Typesetting (numbering, PDF, page numbers, bookmarks) is shared with the
whitepaper builder.
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "docs", "whitepaper"))

import build_whitepaper as W  # noqa: E402
from autodisloc._meta import AUTHOR, VERSION  # noqa: E402
from autodisloc.i18n import set_language  # noqa: E402

EXTRA_CSS = """
pre.code { font-family: "SF Mono", Menlo, Consolas, monospace; font-size: 8.4pt; background: #f6f5f1;
           border: 1px solid #e2e1dc; border-radius: 4px; padding: 7px 10px; margin: 6px 0 10px;
           white-space: pre-wrap; text-align: left; page-break-inside: avoid; line-height: 1.4; }
.quick { border: 1px solid #2a78d6; border-radius: 6px; padding: 8px 14px; margin: 10px 0; background: #f5f8fd; }
.quick ol { margin: 4px 0 2px; }
.tip { font-size: 9.6pt; border-left: 3px solid #1baf7a; background: #f2faf6; padding: 7px 11px; margin: 8px 0; }
kbd { font-family: -apple-system, "Helvetica Neue", Arial, sans-serif; font-size: 8.8pt; border: 1px solid #c9c8c2;
      border-bottom-width: 2px; border-radius: 3px; padding: 0 4px; background: #fff; }
.ui { font-family: -apple-system, "Helvetica Neue", Arial, sans-serif; font-weight: 600; font-size: 9.8pt; }
"""

def build(lang):
    E = lang == "en"
    t = lambda en, tr: en if E else tr
    B = []
    img = lambda name: f"img_{lang}/{name}"

    def H(level, label, en, tr, numbered=True):
        B.append(["h", level, label, t(en, tr), numbered])

    def P(en, tr):
        B.append(["p", t(en, tr)])

    def NOTE(en, tr, css="note"):
        B.append(["note", t(en, tr), css])

    def UL(en, tr, ordered=False):
        B.append(["ul", t(en, tr), ordered])

    def FIG(label, name, en, tr, width=1.0):
        B.append(["fig", label, img(name), t(en, tr), width])

    def TAB(label, en, tr, head, rows, css=""):
        B.append(["tab", label, t(en, tr), head, rows, css])

    def CODE(s):
        B.append(["code", s])

    ui = lambda s: f'<span class="ui">{s}</span>'

    # ================================================================ 1 INTRO
    H(1, "intro", "What AutoDisloc does", "AutoDisloc ne yapar")
    P("AutoDisloc 2 calculates the <b>dislocation density ρ</b>, the <b>Burgers-vector population</b> (fractions of "
      "⟨a⟩, ⟨c⟩ and ⟨c+a⟩ dislocations), the dislocation arrangement parameter <b>M*</b> and the crystallite size "
      "of hcp α/α′ titanium alloys (e.g. Ti-6Al-4V, CP-Ti) from laboratory X-ray diffraction (XRD) patterns. It "
      "reads the data of different diffractometers (Bruker, PANalytical, any two-column file) and works with any "
      "X-ray tube and any line standard. It needs two kinds of measurement:",
      "AutoDisloc 2, laboratuvar X-ışını kırınımı (XRD) desenlerinden hcp α/α′ titanyum alaşımlarının (ör. "
      "Ti-6Al-4V, CP-Ti) <b>dislokasyon "
      "yoğunluğunu ρ</b>, <b>Burgers vektörü popülasyonunu</b> (⟨a⟩, ⟨c⟩ ve ⟨c+a⟩ dislokasyonlarının oranları), "
      "dislokasyon düzen parametresini <b>M*</b> ve kristalit boyutunu hesaplar. Farklı difraktometrelerin "
      "verilerini (Bruker, PANalytical, her türlü iki sütunlu dosya) okur; her X-ışını tüpü ve her çizgi standardıyla "
      "çalışır. İki tür ölçüme ihtiyaç duyar:")
    UL(["<b>Sample patterns</b> of the material to be analysed;",
        "<b>a line-standard pattern</b> (LaB6, Si, CeO2, corundum or another well-crystallised powder) measured "
        "with the same diffractometer settings, from "
        "which the program learns the instrumental broadening. It is needed once per instrument setup."],
       ["Analiz edilecek malzemenin <b>numune desenleri</b>;",
        "aynı difraktometre ayarlarıyla ölçülmüş bir <b>çizgi standardı deseni</b> (LaB6, Si, CeO2, korundum ya da "
        "iyi kristallenmiş başka bir toz). Program "
        "cihaz genişlemesini bundan öğrenir; her cihaz düzeni için bir kez gerekir."])
    P("The results are shown as charts and tables in the program and can be exported as publication-ready figures "
      "(PNG/TIFF 600 dpi, PDF, SVG), an Excel report and a LaTeX table. The mathematics is explained in the "
      "whitepaper; this manual explains how to use the program.",
      "Sonuçlar programda grafik ve tablolar hâlinde gösterilir; yayına hazır şekiller (PNG/TIFF 600 dpi, PDF, SVG), "
      "Excel raporu ve LaTeX tablosu olarak dışa aktarılabilir. Matematik whitepaper'da anlatılır; bu kılavuz "
      "programın nasıl kullanılacağını anlatır.")
    B.append(["note", t(
        "<b>Quick start</b><ol><li>Install and open the program (@sec:install).</li>"
        "<li>Load or build the instrument model (@sec:inst).</li>"
        "<li><span class='ui'>Add…</span> the sample patterns (@sec:samples).</li>"
        "<li>Press <span class='ui'>Run analysis</span> (@sec:run).</li>"
        "<li>Read the <span class='ui'>Summary</span> tab and export the paper package (@sec:export).</li></ol>"
        "Steps 2–4 can also be done with the <span class='ui'>Step-by-step assistant…</span>, which asks for "
        "everything in order (@sec:wizard).",
        "<b>Hızlı başlangıç</b><ol><li>Programı kurun ve açın (@sec:install).</li>"
        "<li>Cihaz modelini yükleyin ya da oluşturun (@sec:inst).</li>"
        "<li><span class='ui'>Ekle…</span> ile numune desenlerini seçin (@sec:samples).</li>"
        "<li><span class='ui'>Analizi başlat</span>'a basın (@sec:run).</li>"
        "<li><span class='ui'>Özet</span> sekmesini okuyun ve makale paketini dışa aktarın (@sec:export).</li></ol>"
        "2–4. adımlar, her şeyi sırayla soran <span class='ui'>Adım adım sihirbaz…</span> ile de yapılabilir "
        "(@sec:wizard)."),
        "quick"])

    # ================================================================ 2 INSTALL
    H(1, "install", "Installation", "Kurulum")
    P("There are three ways to run AutoDisloc. The ready-made applications need nothing else; running from source "
      "needs Python.",
      "AutoDisloc üç yolla çalıştırılabilir. Hazır uygulamalar başka bir şey gerektirmez; kaynaktan çalıştırmak "
      "Python gerektirir.")
    TAB("ways", "Ways of running the program.", "Programı çalıştırma yolları.",
        [t("Way", "Yol"), "macOS", "Windows", t("Requirement", "Gereksinim")],
        [[t("Ready-made application", "Hazır uygulama"), "AutoDisloc2_macOS.zip", "AutoDisloc2_Windows.zip",
          t("none", "yok")],
         [t("From source (double-click)", "Kaynaktan (çift tıklama)"), "AutoDisloc2_Mac.command",
          "AutoDisloc2_Windows.bat", "Python ≥ 3.9"],
         [t("Command line / Python library", "Komut satırı / Python kütüphanesi"), "python -m autodisloc …",
          "python -m autodisloc …", "Python ≥ 3.9"]])
    H(2, "inst_mac", "macOS: ready-made application", "macOS: hazır uygulama")
    UL(["Download <code>AutoDisloc2_macOS.zip</code> from the <i>Releases</i> page of the repository (or take it from "
        "the <code>dist/</code> folder).",
        "Double-click the zip file; <code>AutoDisloc2.app</code> appears. Drag it into <i>Applications</i>.",
        "The application is not signed by Apple, so macOS blocks the first start. Open it once, close the warning, "
        "then go to <i>System Settings › Privacy &amp; Security</i> and press <span class='ui'>Open Anyway</span>. "
        "On macOS 14 and earlier you can instead right-click the app and choose <span class='ui'>Open</span>.",
        "From then on the program starts with a normal double-click."],
       ["Deponun <i>Releases</i> sayfasından <code>AutoDisloc2_macOS.zip</code>'i indirin (ya da <code>dist/</code> "
        "klasöründen alın).",
        "Zip dosyasına çift tıklayın; <code>AutoDisloc2.app</code> oluşur. <i>Uygulamalar</i> klasörüne sürükleyin.",
        "Uygulama Apple tarafından imzalı olmadığı için macOS ilk açılışı engeller. Bir kez açmayı deneyin, uyarıyı "
        "kapatın, sonra <i>Sistem Ayarları › Gizlilik ve Güvenlik</i>'e gidip <span class='ui'>Yine de Aç</span>'a "
        "basın. macOS 14 ve öncesinde uygulamaya sağ tıklayıp <span class='ui'>Aç</span>'ı seçmek de yeterlidir.",
        "Bundan sonra program normal çift tıklamayla açılır."], ordered=True)
    P("If macOS still refuses (for example on a managed computer), the quarantine flag can be removed in Terminal:",
      "macOS yine de izin vermezse (örneğin kurum tarafından yönetilen bir bilgisayarda) karantina işareti "
      "Terminal'de kaldırılabilir:")
    CODE("xattr -dr com.apple.quarantine /Applications/AutoDisloc2.app")
    H(2, "inst_win", "Windows: ready-made application", "Windows: hazır uygulama")
    UL(["Download <code>AutoDisloc2_Windows.zip</code> from the <i>Releases</i> page and extract it "
        "(right-click › <i>Extract All</i>).",
        "Open the extracted <code>AutoDisloc2</code> folder and double-click <code>AutoDisloc2.exe</code>. Keep the "
        "other files in the folder; the program needs them.",
        "If Windows SmartScreen shows <i>Windows protected your PC</i>, click <span class='ui'>More info</span> and "
        "then <span class='ui'>Run anyway</span>.",
        "Optional: right-click <code>AutoDisloc2.exe</code> › <i>Send to › Desktop (create shortcut)</i>."],
       ["<i>Releases</i> sayfasından <code>AutoDisloc2_Windows.zip</code>'i indirin ve açın "
        "(sağ tık › <i>Tümünü ayıkla</i>).",
        "Çıkan <code>AutoDisloc2</code> klasörünü açıp <code>AutoDisloc2.exe</code>'ye çift tıklayın. Klasördeki "
        "diğer dosyaları silmeyin; program onlara ihtiyaç duyar.",
        "Windows SmartScreen <i>Windows bilgisayarınızı korudu</i> uyarısı verirse <span class='ui'>Ek bilgi</span>'ye, "
        "ardından <span class='ui'>Yine de çalıştır</span>'a tıklayın.",
        "İsteğe bağlı: <code>AutoDisloc2.exe</code>'ye sağ tıklayıp <i>Gönder › Masaüstü (kısayol oluştur)</i>."],
       ordered=True)
    P("The Windows application can also be built on a Windows computer with "
      "<code>packaging\\build_windows.bat</code> (it installs the requirements and PyInstaller and writes "
      "<code>dist\\AutoDisloc2\\AutoDisloc2.exe</code>). On GitHub, every published release builds both "
      "applications automatically.",
      "Windows uygulaması bir Windows bilgisayarda <code>packaging\\build_windows.bat</code> ile de derlenebilir "
      "(gereksinimleri ve PyInstaller'ı kurar, <code>dist\\AutoDisloc2\\AutoDisloc2.exe</code>'yi yazar). "
      "GitHub'da yayımlanan her sürüm iki uygulamayı da otomatik derler.")
    H(2, "inst_src", "Running from source", "Kaynaktan çalıştırma")
    UL(["Install Python 3.9 or newer (python.org or Anaconda). On Windows tick <i>Add Python to PATH</i>.",
        "Download the repository (<i>Code › Download ZIP</i> on GitHub) and extract it.",
        "Double-click <code>AutoDisloc2_Mac.command</code> (macOS) or <code>AutoDisloc2_Windows.bat</code> "
        "(Windows). The first start installs the missing packages once."],
       ["Python 3.9 veya daha yenisini kurun (python.org ya da Anaconda). Windows'ta <i>Add Python to PATH</i> "
        "kutusunu işaretleyin.",
        "Depoyu indirin (GitHub'da <i>Code › Download ZIP</i>) ve açın.",
        "<code>AutoDisloc2_Mac.command</code> (macOS) ya da <code>AutoDisloc2_Windows.bat</code> (Windows) dosyasına "
        "çift tıklayın. İlk açılış eksik paketleri bir kez kurar."], ordered=True)
    P("Or in a terminal in the repository folder:", "Ya da depo klasöründe bir terminalde:")
    CODE("python -m pip install -r requirements.txt\npython AutoDisloc2.py")
    NOTE("The program stores the language, the last instrument model and the last folder in the user settings, so it "
         "opens the way you left it.",
         "Program dili, son cihaz modelini ve son klasörü kullanıcı ayarlarında saklar; bu yüzden bıraktığınız "
         "hâliyle açılır.", "tip")

    # ================================================================ 3 DATA
    H(1, "data", "Preparing the measurements", "Ölçümlerin hazırlanması")
    TAB("meas", "Recommended XRD measurement.", "Önerilen XRD ölçümü.",
        [t("Item", "Konu"), t("Recommendation", "Öneri")],
        [[t("Geometry, radiation", "Geometri, ışınım"), t("Bragg–Brentano; Cu Kα (Kα1+Kα2) with Ni β filter or monochromator. "
                                                        "Co, Fe, Cr, Mo or Ag Kα also work (@sec:measure).",
                                                        "Bragg–Brentano; Ni β filtreli ya da monokromatörlü Cu Kα (Kα1+Kα2). "
                                                        "Co, Fe, Cr, Mo veya Ag Kα da kullanılabilir (@sec:measure).")],
         [t("Range", "Aralık"), t("at least 2θ = 30–85° (all eight α reflections 10.0 … 20.1); 20–90° is typical",
                                  "en az 2θ = 30–85° (sekiz α yansımasının tamamı, 10.0 … 20.1); 20–90° yaygındır")],
         [t("Step, time", "Adım, süre"), t("0.01–0.02° step; peak maxima of at least several thousand counts",
                                           "0,01–0,02° adım; pik tepelerinde en az birkaç bin sayım")],
         [t("Data processing", "Veri işleme"), t("<b>none</b>: no Kα2 stripping, no smoothing, no background subtraction",
                                                 "<b>yok</b>: Kα2 ayıklama, yumuşatma ve zemin çıkarma yapılmamalı")],
         [t("Line standard", "Çizgi standardı"), t("same slits, step and time as the samples, ideally on the same day; "
                                                   "LaB6 (NIST SRM 660c) is best, Si (SRM 640f), CeO2 or corundum are "
                                                   "acceptable (@tab:stds)",
                                                   "numunelerle aynı yarıklar, adım ve süre, tercihen aynı gün; en iyisi "
                                                   "LaB6 (NIST SRM 660c), Si (SRM 640f), CeO2 veya korundum kabul "
                                                   "edilebilir (@tab:stds)")],
         [t("Sample", "Numune"), t("flat polished surface; texture is reported by the program (Harris index)",
                                   "düz parlatılmış yüzey; doku program tarafından raporlanır (Harris katsayısı)")]])
    TAB("formats", "File formats and the measurement data read from them automatically.",
        "Dosya biçimleri ve bunlardan otomatik okunan ölçüm bilgileri.",
        [t("Format", "Biçim"), t("Extension", "Uzantı"), t("Read automatically", "Otomatik okunan")],
        [["Bruker DIFFRAC plus RAW 1.01", ".raw", t("λ₁, λ₂, Kα2/Kα1 (0 = stripped), goniometer radius",
                                                  "λ₁, λ₂, Kα2/Kα1 (0 = ayıklanmış), gonyometre yarıçapı")],
         ["Bruker UXD (text)", ".uxd", "λ₁, λ₂, Kα2/Kα1 (_WL1, _WL2, _WLRATIO)"],
         ["PANalytical XRDML", ".xrdml", t("λ₁, λ₂, Kα2/Kα1, goniometer radius, anode", "λ₁, λ₂, Kα2/Kα1, gonyometre yarıçapı, anot")],
         [t("two-column text (2θ, counts)", "iki sütunlu metin (2θ, sayım)"), ".xy .dat .txt .csv",
          t("optional header lines <code># WL1 = 1.5406</code>, <code># WL2 = …</code>, <code># WLRATIO = 0.5</code>, "
            "<code># RADIUS = 250</code> or <code># ANODE = Cu</code>; otherwise Cu Kα, 0.5 and 250 mm are "
            "<i>assumed</i> and marked as such",
            "isteğe bağlı başlık satırları <code># WL1 = 1.5406</code>, <code># WL2 = …</code>, "
            "<code># WLRATIO = 0.5</code>, <code># RADIUS = 250</code> veya <code># ANODE = Cu</code>; yoksa Cu Kα, 0,5 "
            "ve 250 mm <i>varsayılır</i> ve öyle işaretlenir")]])
    P("What a file does not contain is never guessed silently: it is listed as <i>assumed</i> in the assistant, "
      "in <span class='ui'>Measurement data of the selected file…</span> and in the Excel report, and a missing "
      "wavelength produces a warning; if the peaks fit another anode much better, that anode is suggested. Every "
      "value can be corrected by hand (@sec:measure). Other formats (e.g. Bruker "
      "DIFFRAC.SUITE RAW version 4, Rigaku) can be exported from the instrument software as XRDML, UXD or two-column "
      "text with the header lines above.",
      "Dosyada olmayan hiçbir değer sessizce tahmin edilmez: sihirbazda, <span class='ui'>Seçili dosyanın ölçüm "
      "bilgisi…</span> penceresinde ve Excel raporunda <i>varsayıldı</i> olarak listelenir; dalga boyu eksikse uyarı "
      "verilir; pikler başka bir anotla çok daha iyi eşleşiyorsa o anot önerilir. Her değer elle düzeltilebilir "
      "(@sec:measure). Diğer biçimler (ör. Bruker DIFFRAC.SUITE RAW sürüm 4, "
      "Rigaku) cihaz yazılımından XRDML, UXD ya da yukarıdaki başlık satırlarıyla iki sütunlu metin olarak dışa "
      "aktarılabilir.")
    NOTE("Give the program the raw file of the diffractometer. If the data were exported after <i>Strip Kα2</i>, "
         "the program still works (it reads the state from the header or from the option), but the fit is about two "
         "times worse and a background-subtracted file cannot be used at all.",
         "Programa difraktometrenin ham dosyasını verin. Veri <i>Strip Kα2</i> sonrası dışa aktarılmışsa program yine "
         "çalışır (durumu başlıktan ya da seçenekten okur), ama uydurma yaklaşık iki kat kötüleşir; zemini çıkarılmış "
         "bir dosya ise hiç kullanılamaz.", "warn")

    # ================================================================ 4 INTERFACE
    H(1, "ui", "The program window", "Program penceresi")
    P("@fig:main shows the window after an analysis of the two example patterns supplied with the program "
      "(<code>examples/</code>). The numbered parts are explained in @tab:parts.",
      "@fig:main, programla gelen iki örnek desenin (<code>examples/</code>) analizinden sonraki pencereyi gösterir. "
      "Numaralı bölümler @tab:parts'de açıklanmıştır.")
    FIG("main", "01_main.png", "Main window after an analysis. Numbers refer to @tab:parts.",
        "Analiz sonrası ana pencere. Numaralar @tab:parts'e karşılık gelir.")
    parts = [
        ["1", t("Language", "Dil"), t("Switches between Turkish and English; results and warnings are re-shown in the new language.",
                                      "Türkçe ile İngilizce arasında geçiş yapar; sonuçlar ve uyarılar yeni dilde yeniden gösterilir.")],
        ["2", t("Sample", "Numune"), t("Selects which sample the tabs show.", "Sekmelerin hangi numuneyi göstereceğini seçer.")],
        ["3", t("Save this figure…", "Bu grafiği kaydet…"), t("Saves the figure of the open tab (@sec:onefig).", "Açık sekmedeki grafiği kaydeder (@sec:onefig).")],
        ["4", t("Export all (paper package)…", "Tümünü dışa aktar (makale paketi)…"), t("Writes all figures, the Excel report and the tables (@sec:package).",
                                                                                        "Tüm şekilleri, Excel raporunu ve tabloları yazar (@sec:package).")],
        ["5", t("User manual, Whitepaper, About", "Kullanım kılavuzu, Whitepaper, Hakkında"), t("Opens this manual, the mathematical description, and the version and licence information.",
                                                                                                "Bu kılavuzu, matematiksel açıklamayı ve sürüm-lisans bilgisini açar.")],
        ["6", t("Step-by-step assistant…", "Adım adım sihirbaz…"), t("Optional assistant that asks for all data in order (@sec:wizard).", "Tüm bilgileri sırayla soran isteğe bağlı sihirbaz (@sec:wizard).")],
        ["7", t("1 Instrument standard", "1 Cihaz standardı"), t("Instrument model in use; load or build one (@sec:inst).", "Kullanılan cihaz modeli; yükleme ya da oluşturma (@sec:inst).")],
        ["8", t("2 Samples", "2 Numuneler"), t("List of patterns to analyse (@sec:samples).", "Analiz edilecek desenlerin listesi (@sec:samples).")],
        ["9", t("3 Measurement and material", "3 Ölçüm ve malzeme"), t("Radiation, Kα2, goniometer radius, alloy (@sec:measure).", "Radyasyon, Kα2, gonyometre yarıçapı, alaşım (@sec:measure).")],
        ["10", t("4 Options", "4 Seçenekler"), t("Analysis options (@sec:options). The panel scrolls when the window is small.", "Analiz seçenekleri (@sec:options). Pencere küçükse panel kaydırılır.")],
        ["11", t("Run analysis", "Analizi başlat"), t("Starts the analysis; the bar below shows the progress.", "Analizi başlatır; alttaki çubuk ilerlemeyi gösterir.")],
        ["12", t("Tabs", "Sekmeler"), t("Results of the selected sample (@sec:results).", "Seçili numunenin sonuçları (@sec:results).")],
        ["13", t("Headline", "Başlık satırı"), t("The main result ρ of every sample.", "Her numunenin ana sonucu ρ.")],
        ["14", t("Comparison chart", "Karşılaştırma grafiği"), t("ρ of all samples with 95 % intervals.", "Tüm numunelerin %95 aralıklı ρ değerleri.")],
        ["15", t("Summary table", "Özet tablo"), t("Main numbers of every sample (@tab:sumcols).", "Her numunenin ana sayıları (@tab:sumcols).")],
    ]
    TAB("parts", "Parts of the program window.", "Program penceresinin bölümleri.", ["", t("Part", "Bölüm"), t("Function", "Görevi")], parts)
    P("Every chart has the matplotlib toolbar above it: <i>home</i> resets the view, the arrows step through views, "
      "the cross pans, the magnifier zooms into a rectangle, and the disk saves the figure as shown on screen. For "
      "publication-quality files use <span class='ui'>Save this figure…</span> instead.",
      "Her grafiğin üstünde matplotlib araç çubuğu vardır: <i>ev</i> görünümü sıfırlar, oklar görünümler arasında "
      "gezinir, artı işareti kaydırır, büyüteç bir dikdörtgene yakınlaştırır, disk ise şekli ekrandaki hâliyle kaydeder. "
      "Yayın kalitesinde dosya için bunun yerine <span class='ui'>Bu grafiği kaydet…</span>'i kullanın.")

    # ================================================================ 5 STEP BY STEP
    H(1, "steps", "Step-by-step analysis", "Adım adım analiz")
    H(2, "lang", "Choosing the language", "Dil seçimi")
    P("Press <span class='ui'>TR</span> or <span class='ui'>EN</span> at the right of the toolbar. The window is "
      "rebuilt in the chosen language; loaded samples, options and results are kept. Exported files (folder names, "
      "Excel sheets, figure labels) use the language that is active when you export.",
      "Araç çubuğunun sağındaki <span class='ui'>TR</span> ya da <span class='ui'>EN</span>'e basın. Pencere seçilen "
      "dilde yeniden kurulur; yüklü numuneler, seçenekler ve sonuçlar korunur. Dışa aktarılan dosyalar (klasör adları, "
      "Excel sayfaları, şekil etiketleri) dışa aktarma anındaki dili kullanır.")
    H(2, "wizard", "Step-by-step assistant (optional)", "Adım adım sihirbaz (isteğe bağlı)")
    P("The assistant asks for everything an analysis needs, one page at a time, and shows on every page what the "
      "program has read from the files by itself. It is opened with <span class='ui'>Step-by-step assistant…</span> "
      "at the top of the left panel. When you press <span class='ui'>Run analysis</span>, the program also offers "
      "it (<span class='ui'>Open the assistant</span> / <span class='ui'>Run directly</span>); tick "
      "<span class='ui'>Do not ask again</span> to switch the question off (it can be switched on again on the first "
      "page of the assistant). Using it is never required: every setting is also in the left panel.",
      "Sihirbaz, bir analiz için gereken her şeyi sayfa sayfa sorar ve her sayfada programın dosyalardan kendiliğinden "
      "okuduklarını gösterir. Sol panelin üstündeki <span class='ui'>Adım adım sihirbaz…</span> ile açılır. "
      "<span class='ui'>Analizi başlat</span>'a basıldığında program onu ayrıca önerir (<span class='ui'>Sihirbazı "
      "aç</span> / <span class='ui'>Doğrudan hesapla</span>); soruyu kapatmak için <span class='ui'>Bir daha "
      "sorma</span>'yı işaretleyin (sihirbazın ilk sayfasından yeniden açılabilir). Kullanmak hiçbir zaman zorunlu "
      "değildir: tüm ayarlar sol panelde de bulunur.")
    TAB("wzpages", "Pages of the assistant.", "Sihirbazın sayfaları.", [t("Page", "Sayfa"), t("What you do", "Ne yapılır")],
        [[t("1 · Data and measurement", "1 · Veri ve ölçüm bilgileri"),
          t("Add the sample files. The table shows format, λ₁, Kα2/Kα1 and goniometer radius of every file with "
            "their source (<i>from file</i>, <i>assumed</i> in red, or <i>user</i>). Correct radiation, Kα2 or radius "
            "only if they are missing or wrong (@fig:wzdata).",
            "Numune dosyalarını ekleyin. Tablo, her dosyanın biçimini, λ₁, Kα2/Kα1 ve gonyometre yarıçapını kaynağıyla "
            "(<i>dosyadan</i>, kırmızı <i>varsayıldı</i> ya da <i>kullanıcı</i>) gösterir. Radyasyonu, Kα2'yi veya "
            "yarıçapı yalnızca eksik ya da yanlışsa düzeltin (@fig:wzdata).")],
         [t("2 · Material", "2 · Malzeme"),
          t("Choose the alloy preset or enter nominal lattice parameters (@sec:measure).",
            "Hazır alaşımı seçin ya da nominal kafes parametrelerini girin (@sec:measure).")],
         [t("3 · Instrumental broadening", "3 · Cihaz genişlemesi"),
          t("Keep the current instrument model, load a saved one, or build a new one from a standard measurement "
            "with the standard material of your choice; press <span class='ui'>Fit the standard</span> and, if you "
            "like, <span class='ui'>Save model…</span> (@fig:wzinst, @sec:inst). A wavelength that differs from "
            "the samples is shown in red.",
            "Mevcut cihaz modelini kullanın, kayıtlı bir modeli yükleyin ya da seçtiğiniz standart malzemeyle bir "
            "standart ölçümünden yenisini oluşturun; <span class='ui'>Standardı uydur</span>'a ve isterseniz "
            "<span class='ui'>Modeli kaydet…</span>'e basın (@fig:wzinst, @sec:inst). Numunelerden farklı bir dalga "
            "boyu kırmızıyla gösterilir.")],
         [t("4 · Options", "4 · Seçenekler"), t("As in @tab:opts.", "@tab:opts'deki gibi.")],
         [t("5 · Summary", "5 · Özet"),
          t("All settings at a glance; <span class='ui'>Run analysis</span> applies them to the main window and "
            "starts the calculation.",
            "Tüm ayarlar bir bakışta; <span class='ui'>Analizi başlat</span> bunları ana pencereye uygular ve "
            "hesaplamayı başlatır.")]])
    FIG("wzdata", "wz_data.png", "Assistant, page 1: two files with complete measurement data and a plain two-column "
        "file whose wavelength and radius are assumed (red).",
        "Sihirbaz, sayfa 1: ölçüm bilgileri tam iki dosya ve dalga boyu ile yarıçapı varsayılan (kırmızı) düz iki "
        "sütunlu bir dosya.", 0.8)
    FIG("wzinst", "wz_instrument.png", "Assistant, page 3: instrument model from a standard measurement with the "
        "standard material, its lattice parameters and the result of the fit (peaks indexed, zero shift).",
        "Sihirbaz, sayfa 3: standart malzeme, kafes parametreleri ve uydurma sonucuyla (indekslenen pikler, sıfır "
        "kayması) bir standart ölçümünden cihaz modeli.", 0.8)

    H(2, "inst", "Instrument model", "Cihaz modeli")
    P("The instrument model describes the peak widths that the diffractometer itself produces. At the first start the "
      "example model of the program's own diffractometer is loaded (label <i>example</i>). <b>For your own "
      "instrument build your own model</b>:",
      "Cihaz modeli, difraktometrenin kendisinin ürettiği pik genişliklerini tanımlar. İlk açılışta programın kendi "
      "difraktometresine ait örnek model yüklenir (<i>örnek</i> etiketiyle). <b>Kendi cihazınız için kendi modelinizi "
      "oluşturun</b>:")
    UL(["Measure a line standard as recommended in @tab:meas.",
        "Press <span class='ui'>Build from a standard pattern…</span>, choose the standard file and the standard "
        "material (@tab:stds). Enter the lattice parameter of your certificate if you have one. The program finds "
        "and fits all peaks (Kα1+Kα2 doublets) and indexes them with the reflections of the standard.",
        "Save the model as a <code>.json</code> file when asked. The <span class='ui'>Instrument</span> tab shows the "
        "result (@fig:inst).",
        "Next time use <span class='ui'>Load instrument model (.json)…</span>; the last model is also loaded "
        "automatically."],
       ["@tab:meas'teki önerilere göre bir çizgi standardı ölçün.",
        "<span class='ui'>Standart desenden oluştur…</span>'a basıp standart dosyasını ve standart malzemeyi seçin "
        "(@tab:stds). Sertifikanız varsa oradaki kafes parametresini girin. Program tüm pikleri bulur, uydurur "
        "(Kα1+Kα2 ikilileri) ve standardın yansımalarıyla indeksler.",
        "Sorulduğunda modeli <code>.json</code> dosyası olarak kaydedin. Sonuç <span class='ui'>Cihaz</span> sekmesinde "
        "görünür (@fig:inst).",
        "Sonraki seferde <span class='ui'>Cihaz modeli yükle (.json)…</span>'yi kullanın; son model ayrıca otomatik "
        "yüklenir."], ordered=True)
    FIG("inst", "tab_instrument.png", "Instrument tab: Gaussian and Lorentzian component widths of the standard peaks "
        "(points) and the fitted model (lines). The points should lie on smooth lines; isolated outliers are dropped "
        "automatically.",
        "Cihaz sekmesi: standart piklerinin Gauss ve Lorentz bileşen genişlikleri (noktalar) ve uydurulan model "
        "(çizgiler). Noktalar düzgün çizgiler üzerinde olmalıdır; tek tük aykırı noktalar otomatik atılır.", 0.75)
    TAB("stds", "Standard materials. The lattice parameters can be edited; certified values depend on the batch "
        "and the temperature.", "Standart malzemeler. Kafes parametreleri değiştirilebilir; sertifika değerleri "
        "partiye ve sıcaklığa bağlıdır.",
        [t("Standard", "Standart"), t("Space group", "Uzay grubu"), t("Default lattice (Å)", "Varsayılan kafes (Å)"),
         t("Source of the default", "Varsayılanın kaynağı")],
        [["LaB₆", "Pm-3m", "a = 4.156826", t("NIST SRM 660c, certified at 22.5 °C", "NIST SRM 660c, 22,5 °C'de sertifikalı")],
         ["Si", "Fd-3m", "a = 5.431144", t("NIST SRM 640f, certified at 22.5 °C", "NIST SRM 640f, 22,5 °C'de sertifikalı")],
         ["CeO₂", "Fm-3m", "a = 5.4111", t("nominal (SRM 674a information value 5.411102)", "nominal (SRM 674a bilgi değeri 5,411102)")],
         [t("Corundum α-Al₂O₃", "Korundum α-Al₂O₃"), "R-3c", "a = 4.7588, c = 12.9910",
          t("nominal literature value; use the certificate of your plate or powder",
            "nominal literatür değeri; plakanızın ya da tozunuzun sertifikasını kullanın")],
         [t("other / unknown", "diğer / bilinmeyen"), "–", "–",
          t("every peak found is used; no indexing, no zero shift", "bulunan tüm pikler kullanılır; indeksleme ve sıfır kayması yok")]],
        "small")
    P("Indexing has three uses. Peaks that are not reflections of the standard (impurities, Kβ or tungsten lines) "
      "are left out of the width model. If only a few peaks can be indexed, the program warns that the standard "
      "material, its lattice parameter or the radiation is probably wrong. Finally, the difference between observed "
      "and calculated positions gives the <b>zero shift</b> of the goniometer and the specimen displacement of the "
      "standard. The <span class='ui'>Instrument</span> tab and the instrument label show them. Applying the zero "
      "shift to the lattice parameters of the samples is optional (assistant page 3, command-line option "
      "<code>--zero</code>). It is recommended only with a standard of certified lattice parameter: with a nominal "
      "lattice, zero shift and displacement cannot be separated reliably.",
      "İndekslemenin üç yararı vardır. Standardın yansıması olmayan pikler (safsızlık, Kβ ya da tungsten çizgileri) "
      "genişlik modeline alınmaz. Pikler az sayıda indekslenebiliyorsa program, standart malzemenin, kafes "
      "parametresinin ya da radyasyonun muhtemelen yanlış olduğunu bildirir. Son olarak, gözlenen ve hesaplanan "
      "konumların farkı gonyometrenin <b>sıfır kaymasını</b> ve standardın yüzey yer değiştirmesini verir. Bunlar "
      "<span class='ui'>Cihaz</span> sekmesinde ve cihaz etiketinde gösterilir. Sıfır kaymasının numunelerin kafes "
      "parametrelerine uygulanması isteğe bağlıdır (sihirbaz sayfa 3, komut satırında <code>--zero</code>). "
      "Yalnızca kafes parametresi sertifikalı bir standartla önerilir: nominal kafesle sıfır kayması ve yer "
      "değiştirme güvenilir biçimde ayrılamaz.")
    NOTE("Samples and standard must be measured with the same optics. A model from another instrument, other slits "
         "or a much older measurement changes ρ directly (in the example data by up to 30–45 %).",
         "Numuneler ve standart aynı optikle ölçülmelidir. Başka bir cihazın, başka yarıkların ya da çok eski bir "
         "ölçümün modeli ρ'yu doğrudan değiştirir (örnek veride %30–45'e kadar).", "warn")
    H(2, "samples", "Adding samples", "Numune ekleme")
    UL(["<span class='ui'>Add…</span> opens a file dialog; several files can be selected at once.",
        "The file name (without extension) becomes the sample name. <b>Double-click a name to change it</b>, for "
        "example to <i>AB</i>, <i>HT 800 °C</i>. This name appears in all figures and tables.",
        "Hover over a name to see the full file path. <span class='ui'>Remove</span> deletes the selected entries "
        "from the list (not from the disk).",
        "The order of the list is the order of the comparison chart and the tables."],
       ["<span class='ui'>Ekle…</span> bir dosya penceresi açar; birden çok dosya aynı anda seçilebilir.",
        "Dosya adı (uzantısız) numune adı olur. <b>Adı değiştirmek için çift tıklayın</b>, örneğin <i>AB</i>, "
        "<i>HT 800 °C</i>. Bu ad tüm şekillerde ve tablolarda görünür.",
        "Tam dosya yolunu görmek için fareyi adın üzerinde tutun. <span class='ui'>Kaldır</span> seçili girdileri "
        "listeden siler (diskten değil).",
        "Listenin sırası, karşılaştırma grafiğinin ve tabloların sırasıdır."])
    H(2, "measure", "Measurement data and material", "Ölçüm bilgileri ve malzeme")
    P("The group <span class='ui'>3 Measurement and material</span> of the left panel holds what depends on the "
      "instrument and the alloy. The defaults (<i>From file</i>) are right for RAW, UXD and XRDML files.",
      "Sol paneldeki <span class='ui'>3 Ölçüm ve malzeme</span> grubu, cihaza ve alaşıma bağlı ayarları içerir. "
      "Varsayılanlar (<i>Dosyadan</i>) RAW, UXD ve XRDML dosyaları için doğrudur.")
    TAB("meas_set", "Measurement and material settings.", "Ölçüm ve malzeme ayarları.",
        [t("Setting", "Ayar"), t("Default", "Varsayılan"), t("Meaning", "Anlamı")],
        [[t("Radiation", "Radyasyon"), t("From file (automatic)", "Dosyadan (otomatik)"),
          t("Cu, Co, Fe, Cr, Mo or Ag Kα (tabulated wavelengths) or <i>Custom…</i> (λ₁, λ₂, Kα2/Kα1). Needed for "
            "two-column files without header and for files with a wrong entry.",
            "Cu, Co, Fe, Cr, Mo veya Ag Kα (tablo dalga boyları) ya da <i>Özel…</i> (λ₁, λ₂, Kα2/Kα1). Başlıksız iki "
            "sütunlu dosyalar ve yanlış kayıtlı dosyalar için gereklidir.")],
         ["Kα2", t("Automatic (from file)", "Dosyadan otomatik"),
          t("<i>Present</i> for raw data, <i>Stripped</i> for data exported after Kα2 stripping.",
            "Ham veri için <i>Var</i>, Kα2 ayıklandıktan sonra dışa aktarılan veri için <i>Ayıklanmış</i>.")],
         [t("Goniometer R", "Gonyometre R"), t("From file", "Dosyadan"),
          t("Radius of the goniometer (e.g. 240 mm PANalytical, 250 mm Bruker D8). Affects only the specimen "
            "displacement in µm, not ρ. A radius different from that of the standard means another "
            "diffractometer and is reported.", "Gonyometre yarıçapı (ör. PANalytical 240 mm, Bruker D8 250 mm). "
            "Yalnızca µm cinsinden yer değiştirmeyi etkiler, ρ'yu etkilemez. Standardınkinden farklı bir yarıçap "
            "başka bir difraktometre demektir ve bildirilir.")],
         [t("Material", "Malzeme"), "Ti-6Al-4V",
          t("Alloy preset (@tab:mats) or <i>Custom…</i> with α a, c, β a, β phase.",
            "Hazır alaşım (@tab:mats) ya da α a, c, β a ve β fazıyla <i>Özel…</i>.")]])
    TAB("mats", "Material presets. The nominal values only place the peak-fit windows; the lattice parameters are "
        "measured for every sample.", "Hazır alaşımlar. Nominal değerler yalnızca pik pencerelerini yerleştirir; "
        "kafes parametreleri her numunede ölçülür.",
        [t("Preset", "Hazır alaşım"), "α a, c (Å)", "β a (Å)", t("β phase", "β fazı")],
        [["Ti-6Al-4V (α/α′ + β)", "2.925, 4.670", "3.205", t("modelled when present", "varsa modellenir")],
         [t("CP-Ti, grade 1–4 (α)", "CP-Ti, derece 1–4 (α)"), "2.9505, 4.6826", "–", t("not modelled", "modellenmez")],
         [t("custom α-Ti alloy", "özel α-Ti alaşımı"), t("user", "kullanıcı"), t("user", "kullanıcı"),
          t("automatic / always / none", "otomatik / her zaman / yok")]], "small")
    P("By default the nominal lattice is adjusted to the measured pattern (strongest maxima matched to the α "
      "reflections) when it is clearly off, i.e. when it would misplace a reflection by more than 0.35°; any α-Ti "
      "alloy, any wavelength and a goniometer offset are then handled even with the “wrong” preset, while results "
      "obtained with the right preset do not change. The contrast factors, elastic constants and Burgers vectors of the analysis are those of "
      "hcp α/α′ titanium; the program is therefore not meant for other hcp metals (Zr, Mg, …). "
      "<span class='ui'>Measurement data of the selected file…</span> in the sample group shows what was read "
      "from a file and what was assumed.",
      "Varsayılan olarak nominal kafes, belirgin biçimde farklıysa (bir yansımayı 0,35°'den fazla kaydırıyorsa) "
      "ölçülen desene göre ayarlanır (en güçlü tepeler α yansımalarıyla eşleştirilir); böylece “yanlış” hazır alaşım "
      "seçilse bile her α-Ti alaşımı, her dalga boyu ve gonyometre kayması işlenir, doğru hazır alaşımla elde edilen "
      "sonuçlar ise değişmez. Analizdeki kontrast faktörleri, elastik sabitler ve Burgers vektörleri hcp α/α′ titanyuma "
      "aittir; program bu nedenle başka hcp metaller (Zr, Mg, …) için tasarlanmamıştır. Numune grubundaki "
      "<span class='ui'>Seçili dosyanın ölçüm bilgisi…</span> bir dosyadan neyin okunduğunu ve neyin varsayıldığını "
      "gösterir.")
    H(2, "options", "Options", "Seçenekler")
    FIG("sidebar", "02_sidebar.png", "Left panel with the assistant button, the instrument model, the sample list, "
        "the measurement and material settings and the options.",
        "Sihirbaz düğmesi, cihaz modeli, numune listesi, ölçüm ve malzeme ayarları ve seçeneklerle sol panel.", 0.42)
    TAB("opts", "Analysis options. The defaults are right for most analyses.",
        "Analiz seçenekleri. Varsayılanlar çoğu analiz için doğrudur.",
        [t("Option", "Seçenek"), t("Default", "Varsayılan"), t("Meaning", "Anlamı")],
        [[t("Wilkens whole profile", "Wilkens tam profil"), t("on", "açık"),
          t("Main result. Switch off only for a fast preview (mWH and mWA only).",
            "Ana sonuç. Yalnızca hızlı bir ön bakış için kapatın (yalnızca mWH ve mWA).")],
         ["mWH", t("Constrained (physical q)", "Kısıtlı (fiziksel q)"),
          t("<i>Free q1, q2</i> fits q1 and q2 without the constraint, for comparison.",
            "<i>Serbest q1, q2</i>, q1 ve q2'yi kısıt olmadan uydurur; karşılaştırma içindir.")],
         ["Voigt-mWA", t("Voigt transform A(L)", "Voigt dönüşümü A(L)"),
          t("Comparison method only. <i>Muiruri 2020 Eq. 13 / HajyAkbary 2015 Eq. 23</i> reproduces the published "
            "formula of these papers.",
            "Yalnızca karşılaştırma yöntemi. <i>Muiruri 2020 Denk. 13 / HajyAkbary 2015 Denk. 23</i> bu makalelerin "
            "yayımlanmış formülünü yeniden üretir.")],
         [t("Reference M*", "Referans M*"), "2.64",
          t("Used only when ρ and M* cannot be determined together (weak broadening); the interval then covers the "
            "band 1.5–4.0. The default 2.64 is only the geometric mean of the free-fit M* (2.17 and 3.21) of two "
            "well-conditioned samples measured during the development of the program with the example instrument "
            "model; it is not a universal constant. ρ depends on this assumption (a larger M* gives a smaller ρ): "
            "set a value appropriate for your material and instrument, e.g. the free-fit M* of your own "
            "well-conditioned samples. M* in the program's convention (@sec:mstar).",
            "Yalnızca ρ ile M* birlikte belirlenemediğinde (zayıf genişleme) kullanılır; aralık o zaman 1,5–4,0 "
            "bandını kapsar. Varsayılan 2,64, programın geliştirilmesi sırasında örnek cihaz modeliyle ölçülmüş iyi "
            "koşullu iki numunenin serbest uydurma M* değerlerinin (2,17 ve 3,21) geometrik ortalamasından ibarettir; "
            "evrensel bir sabit değildir. ρ bu varsayıma bağlıdır (büyük M* daha küçük ρ verir): malzemenize ve "
            "cihazınıza uygun bir değer girin, ör. kendi iyi koşullu numunelerinizin serbest uydurma M* değeri. "
            "M* programın tanımıyladır (@sec:mstar).")],
         ["Monte Carlo", "100", t("Number of draws for the Voigt-mWA uncertainty; 0 makes the analysis faster.",
                                  "Voigt-mWA belirsizliği için çekim sayısı; 0 analizi hızlandırır.")]])
    H(2, "run", "Running the analysis", "Analizi çalıştırma")
    P("Press <span class='ui'>Run analysis</span>. The bar shows which sample is being processed. The whole-profile "
      "fit takes about 1–4 minutes per sample; samples at the detection limit take longer because the program scans "
      "the profile likelihood for an upper limit. The window stays usable during the analysis. When it is finished "
      "the <span class='ui'>Summary</span> tab opens.",
      "<span class='ui'>Analizi başlat</span>'a basın. Çubuk hangi numunenin işlendiğini gösterir. Tam profil "
      "uydurması numune başına yaklaşık 1–4 dakika sürer; algılama sınırındaki numuneler daha uzun sürer, çünkü "
      "program bir üst sınır için profil olabilirliğini tarar. Pencere analiz sırasında kullanılabilir kalır. Analiz "
      "bitince <span class='ui'>Özet</span> sekmesi açılır.")

    # ================================================================ 6 RESULTS
    H(1, "results", "Reading the results", "Sonuçları okuma")
    P("The <span class='ui'>Sample</span> box in the toolbar selects which sample the tabs show. The headline and "
      "the summary tab show all samples together.",
      "Araç çubuğundaki <span class='ui'>Numune</span> kutusu, sekmelerin hangi numuneyi göstereceğini seçer. Başlık "
      "satırı ve özet sekmesi tüm numuneleri birlikte gösterir.")
    H(2, "summary", "Summary", "Özet")
    FIG("summ", "tab_summary.png", "Summary tab: comparison chart (filled points: whole-profile ρ with 95 % interval; "
        "arrow: 95 % upper limit; open circles: Voigt-mWA for comparison) and summary table.",
        "Özet sekmesi: karşılaştırma grafiği (dolu noktalar: %95 aralıklı tam profil ρ; ok: %95 üst sınır; boş "
        "daireler: karşılaştırma için Voigt-mWA) ve özet tablo.")
    TAB("sumcols", "Columns of the summary table.", "Özet tablonun sütunları.",
        [t("Column", "Sütun"), t("Meaning", "Anlamı")],
        [[t("ρ (m⁻²) and 95 % interval", "ρ (m⁻²) ve %95 aralık"), t("<b>Main result.</b> “&lt; x” means that the dislocation broadening is below the detection limit; x is the 95 % upper limit.",
                                                                        "<b>Ana sonuç.</b> “&lt; x”, dislokasyon genişlemesinin algılama sınırının altında olduğunu gösterir; x %95 üst sınırdır.")],
         [t("How it was determined", "Nasıl belirlendi"), t("<i>free fit, Jacobian</i>: ρ and M* fitted freely (most reliable); <i>M* fixed</i>: weak broadening, the interval contains the M* band; <i>upper limit</i>: detection limit.",
                                                           "<i>serbest uydurma, Jacobian</i>: ρ ve M* serbest uyduruldu (en güvenilir); <i>M* sabit</i>: zayıf genişleme, aralık M* bandını içerir; <i>üst sınır</i>: algılama sınırı.")],
         ["M*", t("Dislocation arrangement parameter M* = Re*·√ρ in the program's convention (small: strongly screened, e.g. dipoles; large: weakly correlated dislocations). Divide by 2.568 to compare with CMWP values (@sec:mstar).",
                  "Dislokasyon düzen parametresi M* = Re*·√ρ, programın tanımıyla (küçük: güçlü perdelenmiş, ör. dipoller; büyük: zayıf ilişkili dislokasyonlar). CMWP değerleriyle karşılaştırmak için 2,568'e bölün (@sec:mstar).")],
         ["h ⟨a⟩, h ⟨c⟩, h ⟨c+a⟩", t("Fractions of the Burgers-vector types (sum 1).", "Burgers vektörü tiplerinin oranları (toplam 1).")],
         ["b²C̄ (nm²)", t("Average contrast factor × b²; ρ is inversely proportional to it.", "Ortalama kontrast faktörü × b²; ρ bununla ters orantılıdır.")],
         ["χ²/dof", t("Goodness of the whole-profile fit; ≈1 is ideal, above 3 the model misses something (@sec:warn).",
                      "Tam profil uydurmasının kalitesi; ≈1 idealdir, 3'ün üstünde model bir şeyi kaçırıyor demektir (@sec:warn).")],
         [t("Voigt-mWA ρ", "Voigt-mWA ρ"), t("Comparison value of the classical method; not for reporting.", "Klasik yöntemin karşılaştırma değeri; raporlamak için değil.")],
         ["q₁, q₂, D", t("Contrast parameters and size from the modified Williamson–Hall analysis.", "Modifiye Williamson–Hall analizinden kontrast parametreleri ve boyut.")],
         ["α a, α c, α c/a, β a", t("Lattice parameters of the phases (Å), @sec:lat.", "Fazların kafes parametreleri (Å), @sec:lat.")]])
    H(2, "mstar", "The arrangement parameter M* and the reference M*", "Düzen parametresi M* ve referans M*")
    P("AutoDisloc evaluates the Wilkens function at η = L/Re*, where Re* = Re/2.877 and Re is the cut-off radius "
      "of the logarithmic mWA form ln(Re/L); it reports Re* and M* = Re*·√ρ. MWP-fit and CMWP use "
      "η = ½·e<sup>−1/4</sup>·L/Re* (Ribárik, Ungár &amp; Gubicza 2001, J. Appl. Cryst. 34, 669, Eq. 4) and report "
      "M* = Re*·√ρ with their Re*. For the same physical state <b>M*(CMWP) = M*(AutoDisloc)/2.568</b> "
      "(2.568 = 2·e<sup>1/4</sup>; the same factor applies to Re*). ρ is the same in both conventions. The "
      "whitepaper (section on the Wilkens function) gives the derivation.",
      "AutoDisloc Wilkens fonksiyonunu η = L/Re* ile hesaplar; Re* = Re/2,877, Re ise mWA'nın logaritmik "
      "ln(Re/L) biçimindeki kesme yarıçapıdır; Re* ve M* = Re*·√ρ raporlanır. MWP-fit ve CMWP "
      "η = ½·e<sup>−1/4</sup>·L/Re* kullanır (Ribárik, Ungár &amp; Gubicza 2001, J. Appl. Cryst. 34, 669, Denk. 4) "
      "ve kendi Re*'larıyla M* = Re*·√ρ raporlar. Aynı fiziksel durum için <b>M*(CMWP) = M*(AutoDisloc)/2,568</b>'dir "
      "(2,568 = 2·e<sup>1/4</sup>; Re* için de aynı çarpan geçerlidir). ρ iki tanımda da aynıdır. Türetme "
      "whitepaper'ın Wilkens fonksiyonu bölümündedir.")
    P("When ρ and M* cannot be fitted together (weak broadening), M* is fixed at the <span class='ui'>Reference "
      "M*</span> of the options and the interval covers the band 1.5–4.0. The default 2.64 is only the geometric "
      "mean of the free-fit M* (2.17 and 3.21) of two well-conditioned samples measured during the development of "
      "the program with the example instrument model. It is not a universal constant: ρ then depends on the "
      "assumed M* (a larger M* gives a smaller ρ), so set a value appropriate for your material and instrument, "
      "for example the free-fit M* of your own well-conditioned samples.",
      "ρ ile M* birlikte uydurulamazsa (zayıf genişleme) M*, seçeneklerdeki <span class='ui'>Referans M*</span> "
      "değerine sabitlenir ve aralık 1,5–4,0 bandını kapsar. Varsayılan 2,64, programın geliştirilmesi sırasında "
      "örnek cihaz modeliyle ölçülmüş iyi koşullu iki numunenin serbest uydurma M* değerlerinin (2,17 ve 3,21) "
      "geometrik ortalamasından ibarettir. Evrensel bir sabit değildir: ρ o zaman varsayılan M*'a bağlıdır (büyük M* "
      "daha küçük ρ verir); malzemenize ve cihazınıza uygun bir değer girin, ör. kendi iyi koşullu "
      "numunelerinizin serbest uydurma M* değeri.")
    H(2, "tabpattern", "Pattern and whole profile", "Desen ve tam profil")
    FIG("pattern", "tab_pattern.png", "Pattern tab: measured pattern (log scale) with the indexed α reflections, the "
        "model and the difference.",
        "Desen sekmesi: indekslenmiş α yansımalarıyla ölçülen desen (log ölçek), model ve fark.")
    FIG("wp", "tab_wp.png", "Whole profile tab: every fitted window with measured points, model and difference. The "
        "difference should scatter around zero without structure.",
        "Tam profil sekmesi: uydurulan her pencerede ölçülen noktalar, model ve fark. Fark, belirgin bir yapı "
        "göstermeden sıfır etrafında dağılmalıdır.")
    P("Check this tab for every sample: systematic wave-like residuals at the peak flanks or a missing shoulder "
      "indicate a second phase, a wrong Kα2 setting or a peak that the model does not know.",
      "Bu sekmeyi her numune için kontrol edin: pik yanlarında sistematik dalgalı artıklar ya da eksik bir omuz, ikinci "
      "bir faza, yanlış bir Kα2 ayarına ya da modelin bilmediği bir pike işaret eder.")
    H(2, "tabmwh", "mWH, mWA and Burgers vector", "mWH, mWA ve Burgers vektörü")
    FIG("mwh", "tab_mwh.png", "mWH tab: (a) peak width against K√C̄ – the points should lie close to the curve; "
        "(b) the contrast parabola in x.",
        "mWH sekmesi: (a) pik genişliğinin K√C̄'ye karşı grafiği – noktalar eğriye yakın olmalıdır; (b) x'e göre "
        "kontrast parabolü.")
    FIG("burg", "tab_burgers.png", "Burgers vector tab: (a) q₁–q₂ plane with the region attainable by Ti slip systems; "
        "(b) Burgers-vector fractions from each method.",
        "Burgers vektörü sekmesi: (a) Ti kayma sistemlerinin ulaşabildiği bölgeyle q₁–q₂ düzlemi; (b) her yöntemin "
        "verdiği Burgers vektörü oranları.")
    P("The <span class='ui'>mWA</span> tab shows the classical Voigt-based Warren–Averbach plots and the "
      "<span class='ui'>Fourier components</span> tab the size and dislocation Fourier factors of the highest-K "
      "reflection; both serve for comparison and for teaching.",
      "<span class='ui'>mWA</span> sekmesi klasik Voigt tabanlı Warren–Averbach grafiklerini, "
      "<span class='ui'>Fourier bileşenleri</span> sekmesi en yüksek K'li yansımanın boyut ve dislokasyon Fourier "
      "çarpanlarını gösterir; ikisi de karşılaştırma ve anlatım içindir.")
    H(2, "lat", "Lattice parameters", "Kafes parametreleri")
    FIG("latfig", "tab_lattice.png", "Lattice parameters tab: α a, α c, c/a and β a of all samples with standard errors.",
        "Kafes parametreleri sekmesi: tüm numunelerin standart hatalarıyla α a, α c, c/a ve β a değerleri.")
    P("The lattice parameters of the hcp α (α′) phase are calculated from the Kα1 positions of the eight α "
      "reflections by Cohen's least-squares method. The method includes a term for the specimen displacement s "
      "(the sample surface lying above or below the focusing circle), the main systematic error of Bragg–Brentano "
      "measurements; s is reported in the Excel report (typically within ±0.3 mm). The β lattice parameter is "
      "computed from every β reflection with a significant intensity (area &gt; 3σ), after the same correction; "
      "when no β peak is found the value stays empty. The errors are standard errors of the fit; they do not "
      "contain the uncertainty of the wavelength or of a zero-point error of the goniometer.",
      "hcp α (α′) fazının kafes parametreleri, sekiz α yansımasının Kα1 konumlarından Cohen en küçük kareler "
      "yöntemiyle hesaplanır. Yöntem, Bragg–Brentano ölçümlerinin başlıca sistematik hatası olan numune yüksekliği "
      "hatası s için (numune yüzeyinin odaklama çemberinin üstünde ya da altında olması) bir terim içerir; s Excel "
      "raporunda verilir (genellikle ±0,3 mm içinde). β kafes parametresi, aynı düzeltmeden sonra anlamlı şiddeti "
      "olan (alan &gt; 3σ) her β yansımasından hesaplanır; β piki bulunmazsa değer boş kalır. Hatalar uydurmanın "
      "standart hatalarıdır; dalga boyunun ya da gonyometrenin sıfır noktası hatasının belirsizliğini içermez.")
    H(2, "warn", "Warnings", "Uyarılar")
    FIG("warnB", "tab_warnings_B.png", "Warnings of example B (no detectable dislocation broadening).",
        "B örneğinin uyarıları (algılanabilir dislokasyon genişlemesi yok).", 0.85)
    TAB("warns", "Frequent warnings and what to do.", "Sık görülen uyarılar ve yapılacaklar.",
        [t("Warning", "Uyarı"), t("Meaning / action", "Anlamı / yapılacak")],
        [[t("Sample/instrument width ratio &lt; 1.5; AT THE DETECTION LIMIT", "Numune/cihaz genişlik oranı &lt; 1.5; ALGILAMA SINIRINDA"),
          t("Peaks hardly broader than the instrument. Report the upper limit; use a better standard or synchrotron data.",
            "Pikler cihazdan pek geniş değil. Üst sınırı raporlayın; daha iyi bir standart ya da senkrotron verisi kullanın.")],
         [t("ρ and M* could not be determined together; M* fixed", "ρ ile M* birlikte belirlenemedi; M* sabitlendi"),
          t("Normal for weakly broadened samples. ρ then depends on the assumed M*; the next line of the warning "
            "explains the default. Set the reference M* for your material and instrument and mention the assumption "
            "when reporting.",
            "Zayıf genişlemeli numunelerde olağandır. ρ o zaman varsayılan M*'a bağlıdır; uyarının sonraki satırı "
            "varsayılan değeri açıklar. Referans M*'ı malzemenize ve cihazınıza göre ayarlayın ve raporlarken "
            "varsayımı belirtin.")],
         [t("The intensities are probably not raw counts", "Şiddetler büyük olasılıkla ham sayım değil"),
          t("The file is in counts per second, normalised or processed. The fit weights and the error intervals "
            "assume raw counts; export the raw counts from the diffractometer software if possible.",
            "Dosya saniye başına sayım, normalize ya da işlenmiş. Uydurma ağırlıkları ve hata aralıkları ham sayım "
            "varsayar; mümkünse difraktometre yazılımından ham sayımları dışa aktarın.")],
         [t("Whole profile χ²/dof &gt; 3", "Tam profil χ²/dof &gt; 3"),
          t("The model misses part of the profile (second phase, stacking faults, composition differences, texture). Look at the Whole profile tab.",
            "Model profilin bir kısmını açıklayamıyor (ikinci faz, istif hataları, bileşim farkları, doku). Tam profil sekmesine bakın.")],
         [t("Pronounced texture (Harris T outside 0.5–2)", "Belirgin doku (Harris T, 0.5–2 dışında)"),
          t("The average contrast factor assumes random orientation; treat h and ρ with care, check with EBSD.",
            "Ortalama kontrast faktörü rastgele yönelim varsayar; h ve ρ'yu dikkatle yorumlayın, EBSD ile kontrol edin.")],
         [t("Measured q outside the attainable region", "Ölçülen q ulaşılabilir bölgenin dışında"),
          t("Concerns the free mWH only; the constrained mWH and the whole profile are not affected.",
            "Yalnızca serbest mWH'yi ilgilendirir; kısıtlı mWH ve tam profil etkilenmez.")],
         [t("Negative slope of Y(L)/L² (Voigt-mWA INVALID)", "Y(L)/L² eğimi negatif (Voigt-mWA GEÇERSİZ)"),
          t("The comparison method failed; the main result is not affected.", "Karşılaştırma yöntemi başarısız oldu; ana sonuç etkilenmez.")],
         [t("Component narrower than the instrument (set to zero)", "Bileşen cihazdan dar (sıfırlandı)"),
          t("That component cannot be resolved; frequent near the detection limit.", "O bileşen çözülemiyor; algılama sınırına yakın numunelerde sıktır.")],
         [t("Peaks outside the K range of the standard", "Pikler standardın K aralığı dışında"),
          t("Measure the standard over the same 2θ range as the samples.", "Standardı numunelerle aynı 2θ aralığında ölçün.")]])
    H(2, "peaks", "Peak table", "Pik tablosu")
    P("The <span class='ui'>Peak table</span> tab lists, for every reflection, the position 2θ, the measured (m) and "
      "instrument-corrected (t) Gaussian and Lorentzian widths in degrees and in K units (nm⁻¹), the physical width "
      "ΔK, the contrast variable x, b²C̄<sub>hkl</sub> and the sample/instrument width ratio. The same table is in "
      "the Excel report.",
      "<span class='ui'>Pik tablosu</span> sekmesi her yansıma için 2θ konumunu, ölçülen (m) ve cihazdan arındırılmış "
      "(t) Gauss ve Lorentz genişliklerini derece ve K biriminde (nm⁻¹), fiziksel genişlik ΔK'yi, kontrast değişkeni "
      "x'i, b²C̄<sub>hkl</sub>'yi ve numune/cihaz genişlik oranını listeler. Aynı tablo Excel raporunda da vardır.")

    # ================================================================ 7 EXPORT
    H(1, "export", "Exporting results", "Sonuçları dışa aktarma")
    H(2, "onefig", "One figure", "Tek bir şekil")
    P("Open the tab, press <span class='ui'>Save this figure…</span> and choose the format in the dialog. On the "
      "<span class='ui'>Summary</span> tab the comparison chart is saved.",
      "Sekmeyi açın, <span class='ui'>Bu grafiği kaydet…</span>'e basın ve pencerede biçimi seçin. "
      "<span class='ui'>Özet</span> sekmesinde karşılaştırma grafiği kaydedilir.")
    TAB("fmts", "Figure formats.", "Şekil biçimleri.", [t("Format", "Biçim"), t("Use", "Kullanım")],
        [["PNG 600 dpi", t("presentations, Word documents", "sunumlar, Word belgeleri")],
         ["TIFF 600 dpi (LZW)", t("journals that require bitmap files", "bitmap dosya isteyen dergiler")],
         [t("PDF vector", "PDF vektör"), t("LaTeX documents, journals that accept vector figures", "LaTeX belgeleri, vektör şekil kabul eden dergiler")],
         [t("SVG vector", "SVG vektör"), t("further editing in Inkscape or Illustrator", "Inkscape ya da Illustrator'da düzenleme")]])
    P("Figures are drawn at journal column widths (8.5 cm single, 17.5 cm double column) with 7–8 pt Arial text, so "
      "they can be inserted at 100 % size.",
      "Şekiller dergi sütun genişliklerinde (tek sütun 8,5 cm, çift sütun 17,5 cm) ve 7–8 pt Arial yazıyla çizilir; "
      "%100 boyutta yerleştirilebilir.")
    H(2, "package", "Paper package", "Makale paketi")
    P("<span class='ui'>Export all (paper package)…</span> asks for a folder and writes:",
      "<span class='ui'>Tümünü dışa aktar (makale paketi)…</span> bir klasör sorar ve şunları yazar:")
    CODE(t("<folder>/\n  figures/\n    png/  pdf/  svg/  tif/\n      00_comparison      comparison chart of all samples\n"
           "      00_instrument      instrument model\n      00_lattice_parameters  lattice parameters of all samples\n      <sample>_1_pattern\n      <sample>_2_whole_profile\n"
           "      <sample>_3_mWH\n      <sample>_4_mWA\n      <sample>_5_burgers\n      <sample>_6_fourier\n"
           "  report.xlsx          full report (see the next section)\n"
           "  table_results.csv    result table for Excel / Origin\n"
           "  table_results.tex    result table for LaTeX\n"
           "  table_lattice.csv / .tex   lattice parameters (α a, c, c/a; β a) with errors",
           "<klasör>/\n  sekiller/\n    png/  pdf/  svg/  tif/\n      00_karsilastirma   tüm numunelerin karşılaştırma grafiği\n"
           "      00_cihaz           cihaz modeli\n      00_kafes_parametreleri  tüm numunelerin kafes parametreleri\n      <numune>_1_desen\n      <numune>_2_tam_profil\n"
           "      <numune>_3_mWH\n      <numune>_4_mWA\n      <numune>_5_burgers\n      <numune>_6_fourier\n"
           "  rapor.xlsx           tam rapor (bir sonraki bölüm)\n"
           "  tablo_sonuclar.csv   Excel / Origin için sonuç tablosu\n"
           "  tablo_sonuclar.tex   LaTeX için sonuç tablosu\n"
           "  tablo_kafes.csv / .tex   hatalarıyla kafes parametreleri (α a, c, c/a; β a)"))
    P("The LaTeX table can be included with <code>\\input{table_results.tex}</code>; it contains ρ with its 95 % "
      "interval, M*, the three h fractions and b²C̄. Upper-limit samples show “&lt; x” and dashes for the undefined "
      "parameters.",
      "LaTeX tablosu <code>\\input{tablo_sonuclar.tex}</code> ile eklenebilir; %95 aralığıyla ρ, M*, üç h oranı ve "
      "b²C̄ içerir. Üst sınır numunelerinde “&lt; x” ve tanımsız parametreler için tire yazar.")
    P("Output files record only the program name and version (e.g. “AutoDisloc " + VERSION + "”) in their metadata.",
      "Çıktı dosyalarının üst verisine yalnızca program adı ve sürümü (ör. “AutoDisloc " + VERSION + "”) yazılır.")
    H(2, "excel", "Excel report", "Excel raporu")
    TAB("sheets", "Sheets of the Excel report (n = sample number in the list).",
        "Excel raporunun sayfaları (n = numunenin listedeki sırası).",
        [t("Sheet", "Sayfa"), t("Content", "İçerik")],
        [[t("Summary", "Özet"), t("one row per sample: all results (whole profile, Voigt-mWA, mWH, 40-combination method, lattice parameters)",
                                  "numune başına bir satır: tüm sonuçlar (tam profil, Voigt-mWA, mWH, 40 kombinasyon yöntemi, kafes parametreleri)")],
         [t("Column help", "Sütun açıklamaları"), t("meaning of every important column", "her önemli sütunun anlamı")],
         [t("Warnings", "Uyarılar"), t("all warnings of all samples", "tüm numunelerin tüm uyarıları")],
         [t("n_Peaks", "n_Pikler"), t("peak table of sample n", "n numunesinin pik tablosu")],
         ["n_mWA", t("Y(L) values of the Voigt-mWA", "Voigt-mWA'nın Y(L) değerleri")],
         ["n_Burgers", t("Burgers-vector population with its range over all sub-system mixtures", "tüm alt sistem karışımları üzerinden aralığıyla Burgers vektörü popülasyonu")],
         [t("n_WholeProfile", "n_TamProfil"), t("measured, model and difference for every data point (for your own plots)", "her veri noktası için ölçülen, model ve fark (kendi grafikleriniz için)")],
         [t("n_Texture", "n_Doku"), t("Harris texture indices", "Harris doku katsayıları")],
         [t("Measurement and material", "Ölçüm ve malzeme"), t("format, radiation, Kα2, radius, range and step of every file, what was assumed, the alloy and the nominal lattice used",
                                                                  "her dosyanın biçimi, radyasyonu, Kα2'si, yarıçapı, aralığı ve adımı, neyin varsayıldığı, alaşım ve kullanılan nominal kafes")],
         [t("Instrument, Instrument peaks", "Cihaz, Cihaz pikleri"), t("instrument model (standard, lattice, wavelength, zero shift) and the fitted, indexed standard peaks",
                                                                       "cihaz modeli (standart, kafes, dalga boyu, sıfır kayması) ve uydurulan, indekslenen standart pikleri")]])

    # ================================================================ 8 CLI
    H(1, "cli", "Command line and Python", "Komut satırı ve Python")
    P("Everything the program does can also be run without the window, for example for many files. In the "
      "repository folder:",
      "Programın yaptığı her şey pencere olmadan da çalıştırılabilir, örneğin çok sayıda dosya için. Depo klasöründe:")
    CODE(t("# instrument model from a line standard\npython -m autodisloc --lang en instrument STANDARD.raw --standard LaB6 -o instrument.json\n\n"
           "# analysis of several samples, Excel report and paper package\npython -m autodisloc --lang en analyze S1.raw S2.raw S3.raw "
           "-c instrument.json -o report.xlsx --package paper_package\n\n"
           "# two-column files measured with Co Kα on a 240 mm goniometer, CP-Ti\n"
           "python -m autodisloc analyze S1.xy -c instrument.json --radiation Co --radius 240 --material CP-Ti",
           "# çizgi standardından cihaz modeli\npython -m autodisloc --lang tr cihaz STANDART.raw -o cihaz.json\n\n"
           "# birden çok numunenin analizi, Excel raporu ve makale paketi\npython -m autodisloc --lang tr analiz N1.raw N2.raw N3.raw "
           "-c cihaz.json -o rapor.xlsx --paket makale_paketi\n\n"
           "# Co Kα ile 240 mm gonyometrede ölçülmüş iki sütunlu dosyalar, CP-Ti\n"
           "python -m autodisloc analiz N1.xy -c cihaz.json --radiation Co --radius 240 --material CP-Ti"))
    TAB("cliopts", "Command-line options.", "Komut satırı seçenekleri.", [t("Option", "Seçenek"), t("Meaning", "Anlamı")],
        [["--lang tr|en", t("language of messages and files", "mesajların ve dosyaların dili")],
         ["--ka2 auto|present|stripped", t("Kα2 state (as in @tab:meas_set)", "Kα2 durumu (@tab:meas_set'deki gibi)")],
         ["--radiation Cu|Co|Fe|Cr|Mo|Ag|λ₁,λ₂[,r]", t("radiation instead of the file value", "dosya değeri yerine radyasyon")],
         ["--radius MM", t("goniometer radius instead of the file value", "dosya değeri yerine gonyometre yarıçapı")],
         ["--standard corundum|LaB6|Si|CeO2|other", t("(instrument) standard material", "(cihaz) standart malzeme")],
         ["--std-lattice A[,C]", t("(instrument) lattice of the standard, Å", "(cihaz) standardın kafesi, Å")],
         ["--material Ti-6Al-4V|CP-Ti, --lattice A,C[,Aβ], --beta auto|yes|no",
          t("alloy preset, nominal lattice, β phase", "hazır alaşım, nominal kafes, β fazı")],
         ["--no-refine", t("keep the nominal lattice (no adjustment to the pattern)", "nominal kafesi koru (desene göre ayarlama yok)")],
         ["--zero", t("apply the zero shift of the standard to the lattice parameters", "standardın sıfır kaymasını kafes parametrelerine uygula")],
         ["--mwh constrained|free", t("mWH mode", "mWH modu")],
         ["--fourier voigt|eq13", t("A(L) formula of the Voigt-mWA (eq13: Muiruri 2020 Eq. 13, for comparison)",
                                    "Voigt-mWA'nın A(L) formülü (eq13: Muiruri 2020 Denk. 13, karşılaştırma için)")],
         ["--mc N", t("Monte Carlo draws", "Monte Carlo çekim sayısı")],
         ["--no-whole-profile", t("skip the whole-profile fit (fast)", "tam profil uydurmasını atla (hızlı)")],
         ["--package FOLDER", t("also write the paper package", "makale paketini de yaz")]])
    P("As a Python library:", "Python kütüphanesi olarak:")
    CODE("from autodisloc import read_pattern, InstrumentModel, analyze, set_language\n"
         "set_language(\"" + lang + "\")\n"
         "inst = InstrumentModel.load(\"instrument.json\")\n"
         "res = analyze(read_pattern(\"examples/synthetic_Ti64_A.xy\"), inst, \"A\")\n"
         "print(res.summary()[\"rho_text\"], res.wp.M_star, res.wp.h)")

    # ================================================================ 9 REPORTING
    H(1, "report", "Interpreting and reporting the results", "Sonuçları yorumlama ve raporlama")
    UL(["<b>Which number?</b> Report the whole-profile ρ with its 95 % interval, M* and the h fractions. The "
        "Voigt-mWA and free mWH values are for comparison only.",
        "<b>M* fixed:</b> state the reference value, the band and where the value comes from, e.g. “M* was fixed "
        "at <i>x</i> (band 1.5–4.0), the free-fit value of well-conditioned samples of the same material measured "
        "with the same instrument”. The default 2.64 is not a universal constant.",
        "<b>Comparing M* with the literature:</b> AutoDisloc's M* = 2.568 × M* of MWP-fit/CMWP (@sec:mstar).",
        "<b>Upper limit:</b> write “ρ &lt; x m⁻² (95 %)”, not a number with an error bar.",
        "<b>χ²/dof well above 1</b> or strong texture: the reported ρ may contain non-dislocation broadening "
        "(composition differences between phases, stacking faults, second-order stresses). Say so, and support "
        "the result with TEM, EBSD or EDS where possible.",
        "<b>Same instrument model</b> for all samples that are compared."],
       ["<b>Hangi sayı?</b> %95 aralığıyla tam profil ρ'yu, M*'ı ve h oranlarını raporlayın. Voigt-mWA ve serbest "
        "mWH değerleri yalnızca karşılaştırma içindir.",
        "<b>M* sabitse:</b> referans değeri, bandı ve değerin kaynağını belirtin, ör. “M*, aynı malzemeden aynı "
        "cihazla ölçülmüş iyi koşullu numunelerin serbest uydurma değeri olan <i>x</i>'e sabitlenmiştir (bant "
        "1,5–4,0)”. Varsayılan 2,64 evrensel bir sabit değildir.",
        "<b>M*'ı literatürle karşılaştırma:</b> AutoDisloc'un M*'ı = 2,568 × MWP-fit/CMWP M*'ı (@sec:mstar).",
        "<b>Üst sınır:</b> hata çubuklu bir sayı değil, “ρ &lt; x m⁻² (%95)” yazın.",
        "<b>χ²/dof 1'in belirgin üstündeyse</b> ya da doku güçlüyse: raporlanan ρ dislokasyon dışı genişleme "
        "(fazlar arası bileşim farkı, istif hataları, ikinci tür gerilmeler) içerebilir. Bunu belirtin ve mümkünse "
        "TEM, EBSD ya da EDS ile destekleyin.",
        "Karşılaştırılan tüm numuneler için <b>aynı cihaz modeli</b>."])
    P("Example text for the methods section:", "Yöntem bölümü için örnek metin:")
    CODE(t("Dislocation densities were determined by X-ray line profile analysis with AutoDisloc 2 [citation].\n"
           "Raw Cu Kα patterns (2θ = 20–90°, step 0.02°) were fitted with the Wilkens dislocation model,\n"
           "a log-normal size distribution and the hexagonal contrast factors of Dragomir and Ungár (2002);\n"
           "the instrumental broadening was obtained from a corundum standard measured with the same optics.\n"
           "95 % intervals were obtained from the fit covariance or, for weakly broadened samples, from a\n"
           "fixed arrangement parameter M* = [value] (band 1.5–4.0; AutoDisloc convention, M*_CMWP = M*/2.568)\n"
           "and the profile likelihood.",
           "Dislokasyon yoğunlukları AutoDisloc 2 [atıf] ile X-ışını çizgi profili analiziyle belirlenmiştir.\n"
           "Ham Cu Kα desenleri (2θ = 20–90°, adım 0,02°) Wilkens dislokasyon modeli, log-normal boyut dağılımı ve\n"
           "Dragomir ve Ungár'ın (2002) hekzagonal kontrast faktörleriyle uydurulmuş; cihaz genişlemesi aynı optikle\n"
           "ölçülen bir korundum standardından elde edilmiştir. %95 aralıkları uydurma kovaryansından ya da zayıf\n"
           "genişlemeli numunelerde sabit düzen parametresi M* = [değer] (bant 1,5–4,0; AutoDisloc tanımı,\n"
           "M*_CMWP = M*/2,568) ve profil olabilirliğinden elde edilmiştir."))

    # ================================================================ 10 FAQ
    H(1, "faq", "Troubleshooting", "Sorun giderme")
    TAB("faqt", "Problems and solutions.", "Sorunlar ve çözümler.", [t("Problem", "Sorun"), t("Solution", "Çözüm")],
        [[t("macOS: “cannot be opened because the developer cannot be verified”", "macOS: “geliştirici doğrulanamadığı için açılamıyor”"),
          t("See @sec:inst_mac (Privacy &amp; Security › Open Anyway).", "@sec:inst_mac'e bakın (Gizlilik ve Güvenlik › Yine de Aç).")],
         [t("Windows: SmartScreen blocks the program", "Windows: SmartScreen programı engelliyor"), t("More info › Run anyway (@sec:inst_win).", "Ek bilgi › Yine de çalıştır (@sec:inst_win).")],
         [t("“Load or build an instrument model first.”", "“Önce cihaz modelini yükleyin veya oluşturun.”"), t("@sec:inst.", "@sec:inst.")],
         [t("The standard cannot be fitted", "Standart uydurulamıyor"), t("Too few peaks: measure the standard over a wider range or with longer counting time.",
                                                                          "Pik sayısı az: standardı daha geniş aralıkta ya da daha uzun sayım süresiyle ölçün.")],
         [t("A file is not accepted", "Bir dosya kabul edilmiyor"), t("Export it from the diffractometer software as XRDML, UXD or two-column text (2θ, counts) with the header lines of @tab:formats.",
                                                                      "Difraktometre yazılımından XRDML, UXD ya da @tab:formats'taki başlık satırlarıyla iki sütunlu metin (2θ, sayım) olarak dışa aktarın.")],
         [t("Warning: “The file contains no wavelength”", "Uyarı: “Dosyada dalga boyu bilgisi yok”"),
          t("Select the radiation (@sec:measure) or add <code># ANODE = …</code> to the file. If the α-Ti peaks "
            "match another anode much better, the warning and the assistant name it (e.g. “Co Kα?”).",
            "Radyasyonu seçin (@sec:measure) ya da dosyaya <code># ANODE = …</code> ekleyin. α-Ti pikleri başka bir "
            "anotla çok daha iyi eşleşiyorsa uyarı ve sihirbaz bunu belirtir (ör. “Co Kα?”).")],
         [t("Warning: “Only n of the m peaks found match …”", "Uyarı: “Bulunan m pikin yalnızca n tanesi … uyuyor”"),
          t("Wrong standard material, lattice parameter or radiation; correct it and build the model again.",
            "Standart malzeme, kafes parametresi ya da radyasyon yanlış; düzeltip modeli yeniden oluşturun.")],
         [t("Warning: goniometer radius of sample and standard differ", "Uyarı: numune ve standardın gonyometre yarıçapı farklı"),
          t("The sample comes from another diffractometer: build an instrument model from a standard measured on "
            "that instrument (@sec:inst). Without it, ρ is not valid.",
            "Numune başka bir difraktometreden geliyor: o cihazda ölçülmüş bir standarttan cihaz modeli oluşturun "
            "(@sec:inst). Aksi hâlde ρ geçerli değildir.")],
         [t("Warning: sample and standard wavelengths differ", "Uyarı: numune ve standart dalga boyları farklı"),
          t("Use a standard measured with the same tube and optics as the samples.",
            "Numunelerle aynı tüp ve optikle ölçülmüş bir standart kullanın.")],
         [t("The analysis takes very long", "Analiz çok uzun sürüyor"), t("Normal at the detection limit; set Monte Carlo to 0 or switch off the whole profile for a preview.",
                                                                          "Algılama sınırında olağandır; ön bakış için Monte Carlo'yu 0 yapın ya da tam profili kapatın.")],
         [t("Very large χ²/dof (&gt; 10)", "Çok büyük χ²/dof (&gt; 10)"), t("Check the Kα2 option and that the file is not background-subtracted or smoothed.",
                                                                           "Kα2 seçeneğini ve dosyanın zemini çıkarılmış ya da yumuşatılmış olmadığını kontrol edin.")],
         [t("Figures look small on screen", "Şekiller ekranda küçük görünüyor"), t("They keep journal proportions; enlarge the window or use the zoom tool. Exported files are unaffected.",
                                                                                     "Dergi oranlarını korurlar; pencereyi büyütün ya da yakınlaştırma aracını kullanın. Dışa aktarılan dosyalar etkilenmez.")],
         [t("Error message after Run analysis", "Analizi başlat sonrası hata mesajı"), t("Copy the message and report it with the data file to the author.",
                                                                                         "Mesajı kopyalayıp veri dosyasıyla birlikte geliştiriciye bildirin.")]])
    H(1, "about", "Licence, citation and contact", "Lisans, atıf ve iletişim")
    P("AutoDisloc is free software under the MIT licence. If you use it in scientific work, please cite it as given "
      "in <code>CITATION.cff</code> of the repository (GitHub: <i>Cite this repository</i>; Zenodo DOI of the release). "
      "The method is described in the whitepaper. Author: " + AUTHOR + ".",
      "AutoDisloc, MIT lisansıyla özgür bir yazılımdır. Bilimsel çalışmalarda kullanırsanız depodaki "
      "<code>CITATION.cff</code>'teki künyeyle kaynak gösterin (GitHub: <i>Cite this repository</i>; sürümün Zenodo "
      "DOI'si). Yöntem whitepaper'da anlatılmıştır. Geliştiren: " + AUTHOR + ".")
    P("<b>Scientific basis and development.</b> The calculation method of AutoDisloc (modified Williamson–Hall, "
      "modified Warren–Averbach and Burgers-vector population analysis) is based on the dislocation-density "
      "measurement method of the author's doctoral thesis: F. Memu, <i>Eklemeli imalat yöntemi ile üretilmiş Ti-6Al-4V alaşımının yüksek gerinme hızlarındaki davranışının deneysel ve sayısal yöntemler ile incelenmesi</i> (Experimental and numerical investigation of the high-strain-rate behaviour of Ti-6Al-4V produced by additive manufacturing), PhD thesis, TOBB University of Economics and Technology, Graduate School of Natural and Applied Sciences, Department of Mechanical Engineering, Ankara, 2025. The conversion "
      "and extension of this method into Python code (including the Wilkens whole-profile fit), the graphical user "
      "interface (GUI), the reports and exports, the packaging, the tests and the documentation (this manual and the "
      "whitepaper) were developed with the assistance of the AI model Claude Opus 5.5 (Anthropic) under the "
      "direction and review of the author. The scientific evaluation of the results and the responsibility for "
      "them rest with the author.",
      "<b>Bilimsel temel ve geliştirme.</b> AutoDisloc'un hesaplama yöntemi (modifiye Williamson–Hall, modifiye "
      "Warren–Averbach ve Burgers vektörü popülasyonu analizi), yazarın doktora tezindeki dislokasyon yoğunluğu "
      "ölçüm yöntemine dayanır: F. Memu, <i>Eklemeli imalat yöntemi ile üretilmiş Ti-6Al-4V alaşımının yüksek gerinme hızlarındaki davranışının deneysel ve sayısal yöntemler ile incelenmesi</i>, Doktora Tezi, TOBB Ekonomi ve Teknoloji Üniversitesi, Fen Bilimleri Enstitüsü, Makina Mühendisliği Anabilim Dalı, Ankara, 2025. Bu yöntemin Python koduna dönüştürülmesi ve "
      "genişletilmesi (Wilkens tam profil uydurması dahil), grafik kullanıcı arayüzü (GUI), raporlar ve dışa "
      "aktarma, paketleme, testler ve belgeler (bu kılavuz ve whitepaper), yazarın yönlendirmesi ve denetiminde "
      "Anthropic'in Claude Opus 5.5 yapay zekâ modelinin yardımıyla geliştirilmiştir. Sonuçların bilimsel "
      "değerlendirmesi ve sorumluluğu yazara aittir.")
    P("<b>Third-party components.</b> AutoDisloc uses NumPy, SciPy, pandas, matplotlib, openpyxl and Pillow, and Qt "
      "through Qt for Python (PySide6) under the GNU LGPLv3 (Qt: Copyright © The Qt Company Ltd. and other "
      "contributors). The ready-made applications contain these components; their licence texts, copies of the GNU "
      "GPL and LGPL and the Qt source-code information are opened with <span class='ui'>About › Third-party "
      "licences</span> and are listed in <code>THIRD-PARTY-NOTICES.md</code> of the repository.",
      "<b>Üçüncü taraf bileşenler.</b> AutoDisloc; NumPy, SciPy, pandas, matplotlib, openpyxl ve Pillow'u, ayrıca Qt'yi "
      "Qt for Python (PySide6) aracılığıyla GNU LGPLv3 lisansıyla kullanır (Qt: Copyright © The Qt Company Ltd. ve "
      "diğer katkıda bulunanlar). Hazır uygulamalar bu bileşenleri içerir; lisans metinleri, GNU GPL ve LGPL "
      "kopyaları ve Qt kaynak kodu bilgisi <span class='ui'>Hakkında › Üçüncü taraf lisansları</span> ile açılır ve "
      "depodaki <code>THIRD-PARTY-NOTICES.md</code> dosyasında listelenir.")
    return B


def front(doc, lang, pages):
    L = lang == "en"
    title = "AutoDisloc 2 — User Manual" if L else "AutoDisloc 2 — Kullanım Kılavuzu"
    sub = ("Dislocation density of hcp titanium alloys from X-ray line profile analysis: installation, use and outputs"
           if L else "X-ışını çizgi profili analiziyle hcp titanyum alaşımlarında dislokasyon yoğunluğu: kurulum, kullanım "
           "ve çıktılar")
    meta = (f"<b>{AUTHOR}</b><br>{'Software version' if L else 'Yazılım sürümü'} {VERSION} · "
            f"{'November 2026' if L else 'Kasım 2026'}")
    note = ("The calculation method of AutoDisloc is based on the dislocation-density measurement method of the "
            "author's doctoral thesis (TOBB University of Economics and Technology, 2025). The Python implementation, the graphical user interface, the reports, "
            "the packaging and the documentation were developed with the assistance of Claude Opus 5.5 (Anthropic) "
            "under the author's direction and review (Section «about»)." if L else
            "AutoDisloc'un hesaplama yöntemi, yazarın doktora tezindeki dislokasyon yoğunluğu ölçüm yöntemine dayanır "
            "(TOBB Ekonomi ve Teknoloji Üniversitesi, 2025). Python uygulaması, grafik kullanıcı arayüzü, raporlar, paketleme ve belgeler, yazarın "
            "yönlendirmesi ve denetiminde Claude Opus 5.5 (Anthropic) yardımıyla geliştirilmiştir (Bölüm «about»).")
    note = note.replace("«about»", doc.labels.get(("sec", "about"), ""))
    return (f'<h1>{title}</h1><div class="meta">{sub}<br>{meta}</div>'
            f'<figure style="--w:0.9"><img src="img_{lang}/00_start.png"></figure>'
            f'<div class="note">{note}</div>'
            f'<div class="pagebreak"></div>'
            f'<h2 id="toc" style="border-top:none">{"Contents" if L else "İçindekiler"}</h2>'
            f'{doc.toc_html(pages, refs=False)}<div class="pagebreak"></div>')


def write(path, doc, lang, pages):
    body = front(doc, lang, pages) + doc.render({}).rsplit('<h2 id="bib">', 1)[0]
    html = W.html_page(body, lang).replace("</style>", EXTRA_CSS + "</style>").replace(
        "AutoDisloc 2 Whitepaper</title>", "AutoDisloc 2 Manual</title>")
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)


def main():
    W.OUT["dir"] = HERE
    for lang in ("tr", "en"):
        set_language(lang)
        blocks = build(lang)
        doc = W.Doc(blocks, {}, lang)
        base = os.path.join(HERE, f"AutoDisloc2_Manual_{lang.upper()}")
        toc_title = "Contents" if lang == "en" else "İçindekiler"
        write(base + ".html", doc, lang, None)
        W.to_pdf(base + ".html", base + ".pdf")
        pages = W.find_pages(base + ".pdf", doc, toc_title)
        for _ in range(2):
            write(base + ".html", doc, lang, pages)
            W.to_pdf(base + ".html", base + ".pdf")
            new = W.find_pages(base + ".pdf", doc, toc_title)
            if new == pages:
                break
            pages = new
        pages.pop("bib", None)
        short = "AutoDisloc 2 — user manual" if lang == "en" else "AutoDisloc 2 — kullanım kılavuzu"
        W.finish_pdf(base + ".pdf", doc, pages, lang, short=short, title="AutoDisloc 2 User Manual")
        missing = [t[2] for i, t in enumerate(doc.toc) if i not in pages]
        print(lang, base + ".pdf", "missing:", missing, flush=True)


if __name__ == "__main__":
    main()
