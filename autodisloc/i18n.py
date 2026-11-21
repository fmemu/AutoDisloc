# SPDX-License-Identifier: MIT
# AutoDisloc 2 - Copyright (c) 2026 Firat Memu
"""Turkish / English texts of the program.

Every user-visible text goes through :func:`tr`. Messages created during an
analysis (warnings, method labels) are :class:`Msg` objects, rendered in the
language active when they are displayed, so switching the language after an
analysis also translates its warnings.
"""

import locale
import os

LANGUAGES = ("tr", "en")
_state = {"lang": None}


def default_language():
    """'tr' on a Turkish system, otherwise 'en' (AUTODISLOC_LANG overrides)."""
    env = os.environ.get("AUTODISLOC_LANG", "").lower()
    if env in LANGUAGES:
        return env
    for v in (os.environ.get("LANG", ""), (locale.getlocale()[0] or "")):
        if v.lower().startswith("tr"):
            return "tr"
    return "en"


def get_language():
    if _state["lang"] is None:
        _state["lang"] = default_language()
    return _state["lang"]


def set_language(lang):
    if lang not in LANGUAGES:
        raise ValueError(lang)
    _state["lang"] = lang


def tr(key, **kw):
    """Text of ``key`` in the active language, formatted with ``kw``."""
    pair = STRINGS.get(key)
    if pair is None:
        return key
    s = pair[0] if get_language() == "tr" else pair[1]
    return s.format(**kw) if kw else s


def _render(v):
    """Messages inside messages are rendered lazily (in the active language)."""
    if isinstance(v, Msg):
        return str(v)
    if isinstance(v, (list, tuple)) and v and all(isinstance(x, Msg) for x in v):
        return "; ".join(str(x) for x in v)
    return v


class Msg:
    """A translatable message; ``str(msg)`` renders it in the active language."""

    __slots__ = ("key", "kw")

    def __init__(self, key, **kw):
        self.key, self.kw = key, kw

    def __str__(self):
        return tr(self.key, **{k: _render(v) for k, v in self.kw.items()})

    def __repr__(self):
        return f"Msg({self.key!r}, {self.kw!r})"

    def __contains__(self, item):
        return item in str(self)

    def startswith(self, prefix):
        return str(self).startswith(prefix)


# key: (Turkish, English)
STRINGS = {
    # ---------------------------------------------------------------- general
    "yes": ("EVET", "YES"),
    "no": ("HAYIR", "NO"),
    "sample_default": ("numune{n}", "sample{n}"),
    "no_warnings": ("Uyarı yok.", "No warnings."),

    # -------------------------------------------------------------- warnings
    "w.few_peaks": ("Yalnızca {n} pik kullanılabildi (en az 5 gerekli).",
                    "Only {n} peaks could be used (at least 5 are required)."),
    "w.width_bound": ("Genişlik alt sınıra dayandı: {hkl}", "Peak width at its lower bound: {hkl}"),
    "w.comp_below": ("{comp} bileşeni cihaz genişliğinden küçük (sıfırlandı): {hkl}",
                     "{comp} component narrower than the instrument (set to zero): {hkl}"),
    "w.ratio_low": ("Numune/cihaz genişlik oranı < 1.5: {hkl}",
                    "Sample/instrument width ratio < 1.5: {hkl}"),
    "w.detection": ("ALGILAMA SINIRINDA: pik genişlemesi cihaz genişlemesine çok yakın.",
                    "AT THE DETECTION LIMIT: peak broadening is very close to the instrumental broadening."),
    "w.outside_std": ("Bazı pikler standardın K aralığının dışında (cihaz modeli ekstrapolasyon).",
                      "Some peaks lie outside the K range of the standard (instrument model extrapolated)."),
    "w.mwh_poor": ("mWH uyumu zayıf (R² = {r2:.2f}).", "Poor mWH fit (R² = {r2:.2f})."),
    "w.q_unphysical": ("Ölçülen q1={q1:.3f}, q2={q2:.3f} Ti kayma sistemlerinin ulaşabildiği bölgenin "
                       "dışında; en yakın fiziksel çözüm kullanıldı.",
                       "Measured q1={q1:.3f}, q2={q2:.3f} lie outside the region attainable by Ti slip "
                       "systems; the closest physical solution was used."),
    "w.chkl_neg": ("Bazı yansımalarda b²C_hkl ≤ 0 çıktı (q değerleri fiziksel değil).",
                   "b²C_hkl ≤ 0 for some reflections (q values are not physical)."),
    "w.mwa_slope": ("Y(L)/L² – ln L eğimi negatif: Voigt-mWA dislokasyon yoğunluğu hesaplanamaz (GEÇERSİZ).",
                    "Negative slope of Y(L)/L² vs ln L: no Voigt-mWA dislocation density (INVALID)."),
    "w.mwa_posY": ("{n} L değerinde Y(L) > 0 (beklenen negatif).",
                   "Y(L) > 0 at {n} L values (negative expected)."),
    "w.mwa_M": ("Wilkens M = {M:.2f} olağan aralığın (0.5–10) dışında.",
                "Wilkens M = {M:.2f} outside the usual range (0.5–10)."),
    "w.mwa_fewL": ("mWA için yeterli L noktası yok.", "Not enough L points for mWA."),
    "w.texture": ("Belirgin doku (Harris T, 0.5–2 dışında): {hkl}. Ortalama kontrast faktörü dokusuz "
                  "numune varsayar; EBSD ile kontrol edin.",
                  "Pronounced texture (Harris T outside 0.5–2): {hkl}. The average contrast factor assumes "
                  "an untextured sample; check with EBSD."),
    "w.mc_unstable": ("Monte Carlo çekimlerinin yalnızca %{pct:.0f}'i geçerli sonuç verdi; sonuç kararsız.",
                      "Only {pct:.0f} % of the Monte Carlo draws gave a valid result; unstable result."),
    "w.L_sensitive": ("Voigt-mWA ρ seçilen L aralığına duyarlı: {lo:.1e} – {hi:.1e} m⁻² (Voigt tabanlı mWA "
                      "model belirsizliği).",
                      "Voigt-mWA ρ depends on the chosen L range: {lo:.1e} – {hi:.1e} m⁻² (model uncertainty "
                      "of the Voigt-based mWA)."),
    "w.wp_failed": ("Tam profil uydurması başarısız: {err}", "Whole-profile fit failed: {err}"),
    "w.wp_bound": ("Tam profil: {name} parametresi sınıra dayandı ({value:.3g}).",
                   "Whole profile: parameter {name} at its bound ({value:.3g})."),
    "w.wp_fixed": ("Tam profil: ρ ile M* birlikte belirlenemedi ({why}); M* = {M} sabitlendi, aralık "
                   "M* = {lo}–{hi} bandını içerir.",
                   "Whole profile: ρ and M* could not be determined together ({why}); M* fixed at {M}, "
                   "the interval covers the band M* = {lo}–{hi}."),
    "w.wp_fixed_ref": ("M* = {M} bir varsayımdır, ölçüm değildir: raporlanan ρ buna bağlıdır (büyük M* daha küçük ρ "
                       "verir). Program varsayılanı 2.64, programın geliştirilmesi sırasında örnek cihaz modeliyle "
                       "ölçülmüş iyi koşullu iki numunenin serbest uydurma M* değerlerinin (2.17 ve 3.21) geometrik "
                       "ortalamasıdır; evrensel bir sabit değildir. Referans M*'ı (Seçenekler) malzemenize ve "
                       "cihazınıza uygun bir değere ayarlayın, ör. kendi iyi koşullu numunelerinizin serbest "
                       "uydurmalarından.",
                       "M* = {M} is an assumption, not a measurement: the reported ρ depends on it (a larger M* gives "
                       "a smaller ρ). The program default 2.64 is the geometric mean of the free-fit M* (2.17 and "
                       "3.21) of two well-conditioned samples measured during the development of the program with "
                       "the example instrument model; it is not a universal constant. Set the reference M* (Options) "
                       "to a value appropriate for your material and instrument, e.g. from free fits of your own "
                       "well-conditioned samples."),
    "w.wp_no_result": ("Tam profil: {step} hiçbir başlangıç değeriyle yapılamadı (önceki iletilere bakın); bu numune "
                       "için tam profil ρ'su ve aralığı raporlanmaz.",
                       "Whole profile: {step} failed for every start value (see the previous messages); no "
                       "whole-profile ρ and no interval are reported for this sample."),
    "w.step_free": ("serbest uydurma", "the free fit"),
    "w.step_fixed": ("M* = {M} sabit uydurma", "the fit with M* fixed at {M}"),
    "w.not_counts": ("Şiddetler büyük olasılıkla ham sayım değil ({why}). Pik ve tam profil uydurmalarındaki 1/√y "
                     "ağırlıkları, χ²/dof ve dolayısıyla raporlanan hata aralıkları ham sayım (Poisson istatistiği) "
                     "varsayar; bu veriler için istatistiksel dayanakları yoktur. Ham sayım verisi önerilir.",
                     "The intensities are probably not raw counts ({why}). The weights 1/√y of the peak and "
                     "whole-profile fits, the χ²/dof and therefore the reported error intervals assume raw counts "
                     "(Poisson statistics) and are not statistically founded for these data. Raw-count data are "
                     "recommended."),
    "nc.cps": ("dosya saniye başına sayım (cps) bildiriyor", "the file declares counts per second"),
    "nc.unit": ("dosya '{u}' birimini bildiriyor", "the file declares the unit '{u}'"),
    "nc.nonint": ("tam sayı olmayan değerler: saniye başına sayım, normalize, ortalanmış veya işlenmiş (ör. Kα2'si "
                  "ayıklanmış) veri", "non-integer values: counts per second, normalised, averaged or processed "
                  "(e.g. Kα2-stripped) data"),
    "nc.low": ("en yüksek şiddet yalnızca {m:.3g}", "highest intensity only {m:.3g}"),
    "iu.counts": ("sayım", "counts"),
    "iu.cps": ("saniye başına sayım (dosyada belirtilmiş)", "counts per second (declared in the file)"),
    "iu.non-integer": ("tam sayı değil (ham sayım değil)", "not integer (not raw counts)"),
    "iu.low": ("düşük (en yüksek < 100)", "low (maximum < 100)"),
    "xl.intensity": ("Şiddet birimi", "Intensity unit"),
    "w.large_error": ("büyük hata", "large error"),
    "w.wp_below": ("Tam profil: dislokasyon genişlemesi algılama sınırının altında; ρ için yalnızca %95 üst "
                   "sınır raporlanır.",
                   "Whole profile: dislocation broadening below the detection limit; only a 95 % upper "
                   "limit of ρ is reported."),
    "w.wp_gof": ("Tam profil χ²/dof = {gof:.1f}: model profilleri sayım istatistiğinin ötesinde sapmayla "
                 "açıklıyor (faz dönüşümü, istif hatası, doku?).",
                 "Whole profile χ²/dof = {gof:.1f}: the model explains the profiles with deviations beyond "
                 "counting statistics (phase transformation, stacking faults, texture?)."),
    "w.std_few": ("Standartta yeterli pik bulunamadı.", "Not enough peaks found in the standard."),

    # ------------------------------------------------------- interval methods
    "im.jacobian": ("serbest uydurma, Jacobian ±1.96σ", "free fit, Jacobian ±1.96σ"),
    "im.upper": ("%95 üst sınır, profil-olabilirlik (M* = {M}, en temkinli)",
                 "95 % upper limit, profile likelihood (M* = {M}, most conservative)"),
    "im.fixed": ("M* = {M} sabit; istatistik + M* {lo}–{hi} bandı",
                 "M* = {M} fixed; statistics + M* band {lo}–{hi}"),

    # ------------------------------------------------------ population labels
    "pop.type_avg": ("Burgers tipi ortalaması (Dragomir 2002 Denk. 10–13)",
                     "Burgers-type average (Dragomir 2002 Eqs. 10–13)"),
    "pop.type_avg_outside": ("Burgers tipi ortalaması – q fiziksel bölge dışında, en yakın çözüm",
                             "Burgers-type average – q outside the physical region, closest solution"),
    "pop.sub_range": ("alt-sistem karışımları aralığının ortası", "centre of the sub-system mixture range"),
    "pop.sub_proj": ("alt-sistem izdüşümü – q fiziksel bölge dışında",
                     "sub-system projection – q outside the physical region"),

    # -------------------------------------------------------- summary columns
    "col.sample": ("Numune", "Sample"),
    "col.rho": ("ρ SONUÇ (m⁻²) [tam profil]", "ρ RESULT (m⁻²) [whole profile]"),
    "col.rho_text": ("ρ SONUÇ (metin)", "ρ RESULT (text)"),
    "col.rho_lo": ("ρ %95 alt (m⁻²)", "ρ 95 % lower (m⁻²)"),
    "col.rho_hi": ("ρ %95 üst (m⁻²)", "ρ 95 % upper (m⁻²)"),
    "col.interval_method": ("Aralık yöntemi", "Interval method"),
    "col.M_star": ("M* (Re*·√ρ)", "M* (Re*·√ρ)"),
    "col.Re_star_nm": ("Re* (nm)", "Re* (nm)"),
    "col.h_a": ("h⟨a⟩ [tam profil]", "h⟨a⟩ [whole profile]"),
    "col.h_c": ("h⟨c⟩ [tam profil]", "h⟨c⟩ [whole profile]"),
    "col.h_ca": ("h⟨c+a⟩ [tam profil]", "h⟨c+a⟩ [whole profile]"),
    "col.b2c_hk0": ("b²C̄hk0 [tam profil] (nm²)", "b²C̄hk0 [whole profile] (nm²)"),
    "col.size_m_nm": ("boyut medyanı m (nm)", "size median m (nm)"),
    "col.size_sigma": ("boyut σ", "size σ"),
    "col.rwp": ("tam profil Rwp (%)", "whole profile Rwp (%)"),
    "col.chi2_dof": ("tam profil χ²/dof", "whole profile χ²/dof"),
    "col.mwa_rho": ("ρ Voigt-mWA (m⁻²)", "ρ Voigt-mWA (m⁻²)"),
    "col.mwa_valid": ("Voigt-mWA geçerli", "Voigt-mWA valid"),
    "col.mwa_p16": ("Voigt-mWA MC %16", "Voigt-mWA MC 16 %"),
    "col.mwa_p84": ("Voigt-mWA MC %84", "Voigt-mWA MC 84 %"),
    "col.mwa_Lmin": ("Voigt-mWA L-aralığı min ρ", "Voigt-mWA L-range min ρ"),
    "col.mwa_Lmax": ("Voigt-mWA L-aralığı max ρ", "Voigt-mWA L-range max ρ"),
    "col.mwa_Re_nm": ("Voigt-mWA Re (nm)", "Voigt-mWA Re (nm)"),
    "col.mwa_M": ("Voigt-mWA M", "Voigt-mWA M"),
    "col.mwa_r2": ("Voigt-mWA R²", "Voigt-mWA R²"),
    "col.mwa_L": ("Voigt-mWA L aralığı (nm)", "Voigt-mWA L range (nm)"),
    "col.mwh_mode": ("mWH modu", "mWH mode"),
    "col.mwh_q1": ("mWH q1", "mWH q1"),
    "col.mwh_q2": ("mWH q2", "mWH q2"),
    "col.mwh_r2": ("mWH R²", "mWH R²"),
    "col.mwh_D_nm": ("D mWH (nm)", "D mWH (nm)"),
    "col.mwh_h_a": ("h⟨a⟩ [mWH]", "h⟨a⟩ [mWH]"),
    "col.mwh_h_c": ("h⟨c⟩ [mWH]", "h⟨c⟩ [mWH]"),
    "col.mwh_h_ca": ("h⟨c+a⟩ [mWH]", "h⟨c+a⟩ [mWH]"),
    "col.mwh_b2c": ("b²C̄hk0 [mWH] (nm²)", "b²C̄hk0 [mWH] (nm²)"),
    "col.mwh_b2c_min": ("b²C̄hk0 min", "b²C̄hk0 min"),
    "col.mwh_b2c_max": ("b²C̄hk0 max", "b²C̄hk0 max"),
    "col.free_q1": ("serbest mWH q1", "free mWH q1"),
    "col.free_q2": ("serbest mWH q2", "free mWH q2"),
    "col.comb_n": ("40 komb. fiziksel çözüm sayısı", "40-comb. number of physical solutions"),
    "col.comb_h_a": ("h⟨a⟩ [40 komb.]", "h⟨a⟩ [40-comb.]"),
    "col.comb_h_c": ("h⟨c⟩ [40 komb.]", "h⟨c⟩ [40-comb.]"),
    "col.comb_h_ca": ("h⟨c+a⟩ [40 komb.]", "h⟨c+a⟩ [40-comb.]"),
    "col.comb_b2c": ("b²C̄hk0 [40 komb.]", "b²C̄hk0 [40-comb.]"),
    "col.a_A": ("α a (Å)", "α a (Å)"),
    "col.a_err": ("α a hata (Å)", "α a error (Å)"),
    "col.c_A": ("α c (Å)", "α c (Å)"),
    "col.c_err": ("α c hata (Å)", "α c error (Å)"),
    "col.ca": ("α c/a", "α c/a"),
    "col.a_beta_A": ("β a (Å)", "β a (Å)"),
    "col.a_beta_err": ("β a hata (Å)", "β a error (Å)"),
    "col.disp_um": ("numune yüksekliği hatası s (µm)", "specimen displacement s (µm)"),
    "help.lattice": ("Kafes parametreleri, Kα1 pik konumlarından Cohen yöntemiyle ve Bragg–Brentano numune "
                     "yüksekliği (yer değiştirme) terimiyle bulunur; hata, uydurmanın standart hatasıdır. β, "
                     "algılanan β yansımalarından (aynı yükseklik düzeltmesiyle) hesaplanır; β piki yoksa boş kalır.",
                     "Lattice parameters from the Kα1 peak positions by Cohen's method with the Bragg–Brentano "
                     "specimen-displacement term; the error is the standard error of the fit. β is computed from "
                     "the detected β reflections (same displacement correction); empty when no β peak is found."),
    "fig.no_beta": ("β piki yok", "no β peak"),
    "fig.lattice_title": ("Faz kafes parametreleri", "Lattice parameters of the phases"),
    "gui.tab_lattice": ("Kafes parametreleri", "Lattice parameters"),
    "gui.hint_lattice": ("α ve β fazlarının kafes parametreleri", "Lattice parameters of the α and β phases"),
    "ex.lattice": ("00_kafes_parametreleri", "00_lattice_parameters"),
    "ex.table_lattice": ("tablo_kafes", "table_lattice"),
    "ex.tex_lattice_caption": ("α ve β fazlarının kafes parametreleri (Cohen yöntemi, numune yüksekliği düzeltmeli).",
                               "Lattice parameters of the α and β phases (Cohen's method with specimen-displacement correction)."),
    "col.fourier_mode": ("Fourier modu", "Fourier mode"),
    "col.ka2": ("Kα2 durumu", "Kα2 state"),
    "ka2.present": ("var (ikili olarak modellendi)", "present (modelled as doublet)"),
    "ka2.stripped": ("ayıklanmış", "stripped"),

    # ----------------------------------------------------------- column help
    "help.rho": ("ANA SONUÇ. Wilkens modelinin ölçülen profillere doğrudan uydurulmasıyla (CMWP tipi tam "
                 "profil analizi) bulunan dislokasyon yoğunluğu.",
                 "MAIN RESULT. Dislocation density from fitting the Wilkens model directly to the measured "
                 "profiles (CMWP-type whole-profile analysis)."),
    "help.rho_text": ("Sonuç ve %95 aralığı yazı olarak; '< x' algılama sınırında üst sınır demektir.",
                      "Result and 95 % interval as text; '< x' is an upper limit at the detection limit."),
    "help.rho_lo": ("Sonucun %95 güven aralığı. Boş alt sınır = algılama sınırı; o zaman yalnızca üst sınır "
                    "raporlanır.",
                    "95 % confidence interval of the result. Empty lower bound = detection limit; only the "
                    "upper limit is reported then."),
    "help.interval_method": ("Jacobian: doğrusal hata yayılımı. Profil-olabilirlik: ρ sabitlenip diğer "
                             "parametreler yeniden uydurularak taranır.",
                             "Jacobian: linear error propagation. Profile likelihood: ρ is fixed and all "
                             "other parameters are refitted along a scan."),
    "help.M_star": ("Dislokasyon düzen parametresi M* = Re*·√ρ, programın tanımıyla: Wilkens fonksiyonu η = L/Re* "
                    "ile hesaplanır; Re* = Re/2.877, Re mWA'nın ln(Re/L) biçimindeki kesme yarıçapıdır. Wilkens ve "
                    "MWP-fit/CMWP tanımında (Ribárik, Ungár & Gubicza 2001, J. Appl. Cryst. 34, 669: η = ½·e^(−1/4)·"
                    "L/Re*) aynı fiziksel durum M*_CMWP = M*/(2·e^(1/4)) = M*/2.568 verir (Re* için de aynı çarpan); "
                    "CMWP değerleriyle karşılaştırmadan önce 2.568'e bölün. ρ tanıma bağlı değildir. M* 0.5–10 "
                    "aralığında sınırlanır. ρ ile M* birlikte uydurulamazsa M* referans değere sabitlenir (varsayılan "
                    "2.64, bant 1.5–4.0: programın geliştirilmesi sırasında örnek cihaz modeliyle ölçülmüş iyi "
                    "koşullu iki numunenin serbest uydurma M* değerlerinin geometrik ortalaması; evrensel bir sabit "
                    "değildir). Bu durumda ρ bu varsayıma bağlıdır (büyük M* daha küçük ρ verir); malzemenize ve "
                    "cihazınıza uygun bir değer girin.",
                    "Dislocation arrangement parameter M* = Re*·√ρ in the program's convention: the Wilkens function "
                    "is evaluated at η = L/Re*, with Re* = Re/2.877 where Re is the cut-off radius of the logarithmic "
                    "mWA form ln(Re/L). In the convention of Wilkens and MWP-fit/CMWP (Ribárik, Ungár & Gubicza 2001, "
                    "J. Appl. Cryst. 34, 669: η = ½·e^(−1/4)·L/Re*) the same physical state has M*_CMWP = "
                    "M*/(2·e^(1/4)) = M*/2.568 (same factor for Re*); divide by 2.568 before comparing with CMWP "
                    "values. ρ does not depend on the convention. M* is bounded to 0.5–10. When ρ and M* cannot be "
                    "fitted together, M* is fixed at the reference value (default 2.64, band 1.5–4.0: the geometric "
                    "mean of the free-fit M* of two well-conditioned samples measured during the development of the "
                    "program with the example instrument model; not a universal constant). ρ then depends on this "
                    "assumption (a larger M* gives a smaller ρ); set a value appropriate for your material and "
                    "instrument."),
    "help.Re_star": ("Etkin dış kesme yarıçapı Re*, programın tanımıyla (Re* = Re/2.877, Re: ln(Re/L) biçimindeki "
                     "yarıçap). CMWP'nin Re*'ı = Re*/2.568.",
                     "Effective outer cut-off radius Re* in the program's convention (Re* = Re/2.877, Re: radius of "
                     "the ln(Re/L) form). The CMWP Re* = Re*/2.568."),
    "help.h": ("Burgers vektörü tiplerinin oranları (toplam 1), tam profil uydurmasından.",
               "Fractions of the Burgers-vector types (sum 1), from the whole-profile fit."),
    "help.b2c_hk0": ("Ortalama b²C_hk0; ρ bununla ters orantılıdır.",
                     "Average b²C_hk0; ρ is inversely proportional to it."),
    "help.size": ("Log-normal kristalit boyut dağılımının medyanı ve logaritmik standart sapması.",
                  "Median and logarithmic standard deviation of the log-normal crystallite-size distribution."),
    "help.gof": ("Uydurma kalitesi. χ²/dof ≈ 1: model profilleri sayım istatistiği düzeyinde açıklıyor.",
                 "Goodness of fit. χ²/dof ≈ 1: the model explains the profiles at the level of counting "
                 "statistics."),
    "help.mwa_rho": ("Muiruri/HajyAkbary yolu (Voigt genişliklerinden A(L), doğru sabitlerle). Karşılaştırma "
                     "içindir; L aralığına duyarlıdır.",
                     "Muiruri/HajyAkbary route (A(L) from Voigt widths, with the correct constants). For "
                     "comparison only; sensitive to the L range."),
    "help.mwa_L": ("Aynı verinin farklı L pencerelerinde verdiği ρ bandı.",
                   "Band of ρ obtained from the same data with different L windows."),
    "help.mwh": ("Kısıtlı mWH: kontrast doğrudan Burgers tipi oranlarıyla yazılır, q her zaman fizikseldir.",
                 "Constrained mWH: the contrast is written with the Burgers-type fractions, q is always "
                 "physical."),
    "help.free": ("q1, q2'nin serbest uydurulması (ulaşılabilir bölgeye kısıtlanmadan); karşılaştırma içindir.",
                  "q1, q2 fitted freely (not constrained to the attainable region); for comparison."),
    "help.comb": ("Burgers tipi başına bir alt-sistem yöntemi (Dragomir & Ungár 2002, Denk. 11–13), serbest q ile: "
                  "4×2×5 = 40 alt-sistem kombinasyonunun fiziksel (tüm h 0–1 arası) çözümlerinin ortalaması. "
                  "Serbest q fiziksel bölgenin dışındaysa çözüm yoktur.",
                  "One sub-system per Burgers type (Dragomir & Ungár 2002, Eqs. 11–13), with the free q: mean of "
                  "the physical solutions (all h in 0–1) of the 4×2×5 = 40 sub-system combinations. No solution "
                  "exists when the free q is outside the physical region."),

    # ------------------------------------------------------------ excel sheets
    "xl.summary": ("Özet", "Summary"),
    "xl.columns": ("Sütun açıklamaları", "Column help"),
    "xl.column": ("Sütun", "Column"),
    "xl.meaning": ("Anlamı", "Meaning"),
    "xl.warnings": ("Uyarılar", "Warnings"),
    "xl.warning": ("Uyarı", "Warning"),
    "xl.peaks": ("Pikler", "Peaks"),
    "xl.burgers": ("Burgers", "Burgers"),
    "xl.wp": ("TamProfil", "WholeProfile"),
    "xl.texture": ("Doku", "Texture"),
    "xl.instrument": ("Cihaz", "Instrument"),
    "xl.instrument_peaks": ("Cihaz pikleri", "Instrument peaks"),
    "xl.parameter": ("Parametre", "Parameter"),
    "xl.value": ("Değer", "Value"),
    "xl.window": ("pencere", "window"),
    "xl.measured": ("ölçülen", "measured"),
    "xl.model": ("model", "model"),
    "xl.diff": ("fark", "difference"),
    "xl.method": ("Yöntem", "Method"),
    "xl.q_physical": ("q fiziksel", "q physical"),
    "xl.q_residual": ("q artık", "q residual"),
    "xl.q_reproduced": ("q yeniden üretilen", "q reproduced"),
    "xl.n_solutions": ("çözüm sayısı", "number of solutions"),
    "xl.inst_name": ("ad", "name"),
    "xl.gauss_coef": ("Gauss katsayıları", "Gaussian coefficients"),
    "xl.lorentz_coef": ("Lorentz katsayıları", "Lorentzian coefficients"),
    "xl.k_range": ("K aralığı", "K range"),

    # ----------------------------------------------------------------- figures
    "fig.measured": ("Ölçülen", "Measured"),
    "fig.wp_model": ("Wilkens tam profil modeli", "Wilkens whole-profile model"),
    "fig.intensity": ("Şiddet (sayım)", "Intensity (counts)"),
    "fig.difference": ("Fark", "Difference"),
    "fig.pattern_title": ("{s}: XRD deseni ve tam profil uydurması", "{s}: XRD pattern and whole-profile fit"),
    "fig.counts": ("Sayım", "Counts"),
    "fig.model": ("Model", "Model"),
    "fig.mwh_fit": ("mWH uyumu, R² = {r2:.3f}", "mWH fit, R² = {r2:.3f}"),
    "fig.slope_invalid": ("eğim ≤ 0: geçersiz", "slope ≤ 0: invalid"),
    "fig.attainable": ("Ti kayma sistemleriyle ulaşılabilir bölge", "Region attainable by Ti slip systems"),
    "fig.avg": ("ort.", "avg."),
    "fig.free_mwh": ("Serbest mWH (q1, q2 serbest)", "Free mWH (q1, q2 free)"),
    "fig.con_mwh": ("Kısıtlı mWH", "Constrained mWH"),
    "fig.wp": ("Tam profil", "Whole profile"),
    "fig.comb": ("40 komb. (n={n})", "40-comb. (n={n})"),
    "fig.h_axis": ("Burgers vektörü oranı h", "Burgers-vector fraction h"),
    "fig.gauss_std": ("Gauss bileşeni (standart)", "Gaussian component (standard)"),
    "fig.lorentz_std": ("Lorentz bileşeni (standart)", "Lorentzian component (standard)"),
    "fig.fwhm_model": ("Toplam FWHM (model)", "Total FWHM (model)"),
    "fig.width_axis": ("Genişlik ($10^{-3}$ nm$^{-1}$)", "Width ($10^{-3}$ nm$^{-1}$)"),
    "fig.inst_title": ("Cihaz genişlemesi", "Instrumental broadening"),
    "fig.wp95": ("Tam profil (Wilkens), %95 aralık", "Whole profile (Wilkens), 95 % interval"),
    "fig.upper": ("%95 üst sınır (algılama sınırı)", "95 % upper limit (detection limit)"),
    "fig.vmwa": ("Voigt-mWA (karşılaştırma)", "Voigt-mWA (comparison)"),
    "fig.rho_axis": ("Dislokasyon yoğunluğu ρ (m$^{-2}$)", "Dislocation density ρ (m$^{-2}$)"),
    "fig.sample_axis": ("Numune", "Sample"),
    "fig.L_axis": ("Fourier uzunluğu L (nm)", "Fourier length L (nm)"),
    "fig.refl_title": ("{hkl} yansıması (K = {K:.2f} nm$^{{-1}}$)", "{hkl} reflection (K = {K:.2f} nm$^{{-1}}$)"),
    "fig.AS": ("$A^S(L)$ boyut", "$A^S(L)$ size"),
    "fig.AD": ("$A^D(L)$ dislokasyon (Wilkens)", "$A^D(L)$ dislocations (Wilkens)"),
    "fig.ASAD": ("$A^S A^D$ fiziksel", "$A^S A^D$ physical"),
    "fig.lnapprox": ("ln(Re/L) (mWA yaklaşımı)", "ln(Re/L) (mWA approximation)"),

    # ------------------------------------------------------------------ export
    "ex.figures": ("sekiller", "figures"),
    "ex.report": ("rapor.xlsx", "report.xlsx"),
    "ex.table": ("tablo_sonuclar", "table_results"),
    "ex.compare": ("00_karsilastirma", "00_comparison"),
    "ex.instrument": ("00_cihaz", "00_instrument"),
    "ex.pattern": ("1_desen", "1_pattern"),
    "ex.wp": ("2_tam_profil", "2_whole_profile"),
    "ex.burgers": ("5_burgers", "5_burgers"),
    "ex.fourier": ("6_fourier", "6_fourier"),
    "ex.tex_caption": ("X-ışını çizgi profili analizinden dislokasyon yoğunluğu ve Burgers vektörü "
                       "popülasyonu (Wilkens tam profil uydurması).",
                       "Dislocation density and Burgers-vector population from X-ray line profile analysis "
                       "(Wilkens whole-profile fit)."),
    "ex.t_sample": ("Numune", "Sample"),

    # --------------------------------------------------------------------- GUI
    "gui.subtitle": ("XRD dislokasyon yoğunluğu (titanyum alaşımları)", "XRD dislocation density (titanium alloys)"),
    "gui.version": ("sürüm {v} · mWH + mWA + Wilkens tam profil", "version {v} · mWH + mWA + Wilkens whole profile"),
    "gui.sample": ("  Numune: ", "  Sample: "),
    "gui.save_fig": ("Bu grafiği kaydet…", "Save this figure…"),
    "gui.export_all": ("Tümünü dışa aktar (makale paketi)…", "Export all (paper package)…"),
    "gui.whitepaper": ("Whitepaper", "Whitepaper"),
    "gui.manual": ("Kullanım kılavuzu", "User manual"),
    "gui.about": ("Hakkında", "About"),
    "gui.lang_tip": ("Dil / Language", "Language / Dil"),
    "gui.start_hint": ("Numune ekleyip analizi başlatın.", "Add samples and start the analysis."),
    "gui.compare_hint": ("Karşılaştırma grafiği analizden sonra görünür.",
                         "The comparison chart appears after the analysis."),
    "gui.tab_summary": ("Özet", "Summary"),
    "gui.tab_pattern": ("Desen", "Pattern"),
    "gui.tab_wp": ("Tam profil", "Whole profile"),
    "gui.tab_mwh": ("mWH", "mWH"),
    "gui.tab_mwa": ("mWA", "mWA"),
    "gui.tab_burgers": ("Burgers vektörü", "Burgers vector"),
    "gui.tab_fourier": ("Fourier bileşenleri", "Fourier components"),
    "gui.tab_instrument": ("Cihaz", "Instrument"),
    "gui.tab_warnings": ("Uyarılar", "Warnings"),
    "gui.tab_peaks": ("Pik tablosu", "Peak table"),
    "gui.hint_pattern": ("Ölçülen desen ve model", "Measured pattern and model"),
    "gui.hint_wp": ("Her pik penceresinde Wilkens modeli", "Wilkens model in every peak window"),
    "gui.hint_mwh": ("Modifiye Williamson–Hall", "Modified Williamson–Hall"),
    "gui.hint_mwa": ("Voigt tabanlı modifiye Warren–Averbach (karşılaştırma)",
                     "Voigt-based modified Warren–Averbach (comparison)"),
    "gui.hint_burgers": ("q₁–q₂ düzlemi ve h kesirleri", "q₁–q₂ plane and h fractions"),
    "gui.hint_fourier": ("A(L) = Aˢ·Aᴰ", "A(L) = Aˢ·Aᴰ"),
    "gui.hint_instrument": ("Standart genişlikleri", "Widths of the standard"),
    "gui.g_instrument": ("1  Cihaz standardı", "1  Instrument standard"),
    "gui.not_loaded": ("Yüklenmedi", "Not loaded"),
    "gui.load_inst": ("Cihaz modeli yükle (.json)…", "Load instrument model (.json)…"),
    "gui.build_inst": ("Standart desenden oluştur…", "Build from a standard pattern…"),
    "gui.inst_label": ("{name}\nK aralığı {k0:.1f}–{k1:.1f} nm⁻¹", "{name}\nK range {k0:.1f}–{k1:.1f} nm⁻¹"),
    "gui.inst_example": (" (örnek: bu çalışmanın difraktometresi)", " (example: diffractometer of this work)"),
    "gui.g_samples": ("2  Numuneler", "2  Samples"),
    "gui.add": ("Ekle…", "Add…"),
    "gui.remove": ("Kaldır", "Remove"),
    "gui.g_options": ("4  Seçenekler", "4  Options"),
    "gui.opt_wp": ("Wilkens tam profil (ana sonuç)", "Wilkens whole profile (main result)"),
    "gui.mwh_con": ("Kısıtlı (fiziksel q)", "Constrained (physical q)"),
    "gui.mwh_free": ("Serbest q1, q2", "Free q1, q2"),
    "gui.four_voigt": ("Voigt dönüşümü A(L)", "Voigt transform A(L)"),
    "gui.four_eq13": ("Muiruri 2020 Denk. 13 / HajyAkbary 2015 Denk. 23",
                      "Muiruri 2020 Eq. 13 / HajyAkbary 2015 Eq. 23"),
    "gui.ka2": ("Kα2", "Kα2"),
    "gui.ka2_auto": ("Dosyadan otomatik", "Automatic (from file)"),
    "gui.ka2_present": ("Var (ham veri)", "Present (raw data)"),
    "gui.ka2_stripped": ("Ayıklanmış (strip Kα2)", "Stripped (Kα2 removed)"),
    "gui.ka2_tip": ("Ham veri önerilir: program her piki Kα1+Kα2 ikilisi olarak modeller.",
                    "Raw data recommended: every peak is modelled as a Kα1+Kα2 doublet."),
    "gui.ref_M": ("Referans M*", "Reference M*"),
    "gui.ref_M_tip": ("ρ ile M* birlikte belirlenemezse kullanılan M* (aralık o zaman 1.5–4.0 bandını kapsar). "
                      "Varsayılan 2.64, programın geliştirilmesi sırasında örnek cihaz modeliyle ölçülmüş iyi koşullu "
                      "iki numunenin serbest uydurma M* değerlerinin (2.17 ve 3.21) geometrik ortalamasıdır; evrensel "
                      "bir sabit değildir. ρ bu varsayıma bağlıdır (büyük M* daha küçük ρ verir): malzemenize ve "
                      "cihazınıza uygun bir değer girin, ör. kendi iyi koşullu numunelerinizin serbest uydurmalarından. "
                      "M* programın tanımıyladır (CMWP M* = M*/2.568).",
                      "M* used when ρ and M* cannot be determined together (the interval then covers the band "
                      "1.5–4.0). The default 2.64 is the geometric mean of the free-fit M* (2.17 and 3.21) of two "
                      "well-conditioned samples measured during the development of the program with the example "
                      "instrument model; it is not a universal constant. ρ depends on this assumption (a larger M* "
                      "gives a smaller ρ): set a value suitable for your material and instrument, e.g. from free fits "
                      "of your own well-conditioned samples. M* in the program's convention (CMWP M* = M*/2.568)."),
    "gui.fig_failed": ("Grafik çizilemedi ({tab}): {err}", "Figure could not be drawn ({tab}): {err}"),
    "gui.unreadable": ("Okunamadı: {f}", "Cannot be read: {f}"),
    "gui.no_wp": ("Bu numune için tam profil sonucu yok (Uyarılar sekmesine bakın).",
                  "No whole-profile result for this sample (see the Warnings tab)."),
    "gui.mc": ("Monte Carlo", "Monte Carlo"),
    "gui.run": ("Analizi başlat", "Run analysis"),
    "gui.note": ("Bir numunenin tam profil uydurması 1–4 dakika sürebilir.",
                 "The whole-profile fit of one sample may take 1–4 minutes."),
    "gui.dlg_inst": ("Cihaz modeli", "Instrument model"),
    "gui.dlg_std": ("Standart deseni (korundum, LaB6, Si, CeO2, …)", "Standard pattern (corundum, LaB6, Si, CeO2, …)"),
    "gui.std_failed": ("Standart uydurulamadı:\n{e}", "The standard could not be fitted:\n{e}"),
    "gui.dlg_save_inst": ("Cihaz modelini kaydet", "Save instrument model"),
    "gui.inst_suffix": ("_cihaz.json", "_instrument.json"),
    "gui.dlg_samples": ("Numune desenleri", "Sample patterns"),
    "gui.file_filter": ("XRD verisi (*.raw *.RAW *.uxd *.UXD *.xrdml *.XRDML *.xy *.XY *.dat *.txt *.csv);;"
                        "Tüm dosyalar (*)",
                        "XRD data (*.raw *.RAW *.uxd *.UXD *.xrdml *.XRDML *.xy *.XY *.dat *.txt *.csv);;"
                        "All files (*)"),
    "gui.item_tip": ("{p}\n(Adı grafiklerde ve tablolarda kullanılır; çift tıklayıp değiştirin.)",
                     "{p}\n(The name is used in figures and tables; double-click to change it.)"),
    "gui.need_samples": ("Önce numune deseni ekleyin.", "Add sample patterns first."),
    "gui.need_inst": ("Önce cihaz modelini yükleyin veya oluşturun.", "Load or build an instrument model first."),
    "gui.progress": ("{name}: pikler, mWH, mWA ve tam profil uydurması…",
                     "{name}: peaks, mWH, mWA and whole-profile fit…"),
    "gui.done": ("Tamamlandı", "Finished"),
    "gui.error": ("Hata oluştu.", "An error occurred."),
    "gui.no_fig": ("Bu sekmede kaydedilecek grafik yok.", "There is no figure to save on this tab."),
    "gui.dlg_save_fig": ("Grafiği kaydet", "Save figure"),
    "gui.fig_name": ("sekil.png", "figure.png"),
    "gui.fig_filter": ("PNG 600 dpi (*.png);;TIFF 600 dpi (*.tif);;PDF vektör (*.pdf);;SVG vektör (*.svg)",
                       "PNG 600 dpi (*.png);;TIFF 600 dpi (*.tif);;PDF vector (*.pdf);;SVG vector (*.svg)"),
    "gui.saved": ("Kaydedildi: {p}", "Saved: {p}"),
    "gui.need_run": ("Önce analiz yapın.", "Run an analysis first."),
    "gui.dlg_package": ("Makale paketi için klasör", "Folder for the paper package"),
    "gui.package_done": ("Makale paketi yazıldı: {d}", "Paper package written: {d}"),
    "gui.headline": ("{s}: ρ = {v} m⁻²", "{s}: ρ = {v} m⁻²"),
    "gui.h_sample": ("Numune", "Sample"),
    "gui.h_rho": ("ρ (m⁻²) ve %95 aralık", "ρ (m⁻²) and 95 % interval"),
    "gui.h_method": ("Nasıl belirlendi", "How it was determined"),
    "gui.no_whitepaper": ("Dosya bulunamadı:\n{p}", "File not found:\n{p}"),
    "gui.about_text": (
        "<h3>AutoDisloc {v}</h3>"
        "<p>X-ışını çizgi profili analiziyle hcp α/α′ titanyum alaşımlarında (ör. Ti-6Al-4V, CP-Ti) dislokasyon yoğunluğu: modifiye "
        "Williamson–Hall, modifiye Warren–Averbach ve Wilkens tam profil uydurması.</p>"
        "<p><b>Geliştiren:</b> Fırat Memu<br>"
        "<b>Lisans:</b> MIT<br>"
        "Bilimsel çalışmalarda kullanırsanız lütfen yazılımı CITATION.cff dosyasındaki künyeyle kaynak "
        "gösterin.</p>"
        "<p><b>Üçüncü taraf bileşenler.</b> Bu program Qt'yi (Qt for Python / PySide6 aracılığıyla) GNU LGPLv3 "
        "lisansıyla kullanır. Qt: Copyright © The Qt Company Ltd. ve diğer katkıda bulunanlar. NumPy, SciPy, "
        "pandas, matplotlib, openpyxl ve Pillow kendi lisanslarıyla kullanılır. Lisans metinleri, GNU GPL ve "
        "LGPL kopyaları ve Qt kaynak kodu bilgisi için <i>Üçüncü taraf lisansları</i> düğmesine basın.</p>",
        "<h3>AutoDisloc {v}</h3>"
        "<p>Dislocation density of hcp α/α′ titanium alloys (e.g. Ti-6Al-4V, CP-Ti) from X-ray line profile analysis: modified "
        "Williamson–Hall, modified Warren–Averbach and Wilkens whole-profile fitting.</p>"
        "<p><b>Developed by:</b> Fırat Memu<br>"
        "<b>License:</b> MIT<br>"
        "If you use it in scientific work, please cite the software as given in CITATION.cff.</p>"
        "<p><b>Third-party components.</b> This program uses Qt (through Qt for Python / PySide6) under the "
        "GNU LGPLv3. Qt: Copyright © The Qt Company Ltd. and other contributors. NumPy, SciPy, pandas, matplotlib, "
        "openpyxl and Pillow are used under their own licences. Press <i>Third-party licences</i> for the licence "
        "texts, copies of the GNU GPL and LGPL and the Qt source-code information.</p>"),
    "gui.third_party": ("Üçüncü taraf lisansları", "Third-party licences"),

    # --------------------------------------------------------------------- CLI
    "cli.inst_help": ("Standart numuneden cihaz genişleme modeli", "Instrument broadening model from a standard"),
    "cli.an_help": ("Dislokasyon yoğunluğu analizi", "Dislocation density analysis"),
    "cli.inst_saved": ("Cihaz modeli kaydedildi: {p}", "Instrument model saved: {p}"),
    "cli.report": ("Rapor: {p}", "Report: {p}"),
    "cli.package": ("Makale paketi: {p}", "Paper package: {p}"),
    "cli.no_wp": ("Wilkens tam profil uydurmasını atla", "Skip the Wilkens whole-profile fit"),
    "cli.line": ("{s}: ρ = {rho} m⁻²  [{method}]; M* = {M}; h⟨a⟩ = {ha}; Voigt-mWA = {mwa} ({valid})",
                 "{s}: ρ = {rho} m⁻²  [{method}]; M* = {M}; h⟨a⟩ = {ha}; Voigt-mWA = {mwa} ({valid})"),
}


# ---------------------------------------------------------------------------
# Measurement metadata, standards, materials and the step-by-step assistant
STRINGS.update({
    # warnings
    "w.wl_assumed": ("Dosyada dalga boyu bilgisi yok; λ₁ = {wl:.5f} Å (Cu Kα) varsayıldı. Farklı bir tüp "
                     "kullanıldıysa radyasyonu \"Ölçüm ve malzeme\" bölümünden seçin.",
                     "The file contains no wavelength; λ₁ = {wl:.5f} Å (Cu Kα) was assumed. If another tube was "
                     "used, select the radiation under \"Measurement and material\"."),
    "w.wl_guess": ("Pikler {anode} Kα ile çok daha iyi eşleşiyor ({n} α yansıması); radyasyon olarak {anode} Kα "
                   "seçilmesi gerekebilir.",
                   "The peaks match {anode} Kα much better ({n} α reflections); the radiation probably has to be "
                   "set to {anode} Kα."),
    "wz.guess": ("{anode} Kα?", "{anode} Kα?"),
    "w.radius_mismatch": ("Numunenin gonyometre yarıçapı ({r:.0f} mm) cihaz standardınınkinden ({r_std:.0f} mm) "
                          "farklı: numune başka bir difraktometrede ölçülmüş görünüyor. Cihaz genişlemesi aynı "
                          "difraktometrede ölçülmüş bir standarttan alınmalıdır; aksi hâlde ρ geçersizdir.",
                          "The goniometer radius of the sample ({r:.0f} mm) differs from that of the instrument "
                          "standard ({r_std:.0f} mm): the sample seems to have been measured on another "
                          "diffractometer. The instrumental broadening must come from a standard measured on the same "
                          "diffractometer; otherwise ρ is not valid."),
    "w.wl_mismatch": ("Numunenin dalga boyu (λ₁ = {wl:.5f} Å) cihaz standardınınkinden (λ₁ = {wl_std:.5f} Å) farklı. "
                      "Cihaz genişlemesi aynı tüp ve optikle ölçülmüş bir standarttan alınmalıdır.",
                      "The sample wavelength (λ₁ = {wl:.5f} Å) differs from that of the instrument standard "
                      "(λ₁ = {wl_std:.5f} Å). The instrumental broadening must come from a standard measured with "
                      "the same tube and optics."),
    "w.std_mismatch": ("Bulunan {m} pikin yalnızca {n} tanesi {std} yansımalarına uyuyor (λ₁ = {wl:.5f} Å). "
                       "Standart malzemeyi, kafes parametresini ve radyasyonu kontrol edin.",
                       "Only {n} of the {m} peaks found match reflections of {std} (λ₁ = {wl:.5f} Å). Check the "
                       "standard material, its lattice parameter and the radiation."),
    "w.std_unindexed": ("Standarda ait olmayan pikler kullanılmadı: {peaks}",
                        "Peaks that do not belong to the standard were not used: {peaks}"),
    "inst.zero": ("Sıfır kayması {z} ({n}/{m} pik indekslendi)", "Zero shift {z} ({n}/{m} peaks indexed)"),

    # metadata
    "meta.format": ("Biçim", "Format"),
    "meta.xy": ("2 sütunlu metin", "2-column text"),
    "meta.anode": ("Anot", "Anode"),
    "meta.wl1": ("λ₁ (Kα1)", "λ₁ (Kα1)"),
    "meta.wl2": ("λ₂ (Kα2)", "λ₂ (Kα2)"),
    "meta.ka2": ("Kα2/Kα1", "Kα2/Kα1"),
    "meta.radius": ("Gonyometre yarıçapı", "Goniometer radius"),
    "meta.range": ("2θ aralığı", "2θ range"),
    "meta.step": ("Adım", "Step"),
    "meta.points": ("Nokta sayısı", "Points"),
    "meta.file": ("dosyadan", "from file"),
    "meta.assumed": ("varsayıldı", "assumed"),
    "meta.user": ("kullanıcı", "user"),
    "meta.source": ("Kaynak", "Source"),
    "meta.title": ("Ölçüm bilgisi: {f}", "Measurement data: {f}"),

    # sidebar
    "gui.g_measure": ("3  Ölçüm ve malzeme", "3  Measurement and material"),
    "gui.radiation": ("Radyasyon", "Radiation"),
    "gui.rad_file": ("Dosyadan (otomatik)", "From file (automatic)"),
    "gui.rad_custom": ("Özel…", "Custom…"),
    "gui.rad_custom_set": ("Özel: λ₁ = {wl1:.5f} Å", "Custom: λ₁ = {wl1:.5f} Å"),
    "gui.rad_tip": ("Dalga boyu RAW, UXD ve XRDML dosyalarından okunur. Yalnızca dosyada yoksa (düz xy) veya "
                    "yanlışsa değiştirin.",
                    "The wavelength is read from RAW, UXD and XRDML files. Change it only if it is missing "
                    "(plain xy) or wrong."),
    "gui.radius": ("Gonyometre R", "Goniometer R"),
    "gui.radius_file": ("Dosyadan", "From file"),
    "gui.radius_tip": ("Bragg–Brentano gonyometre yarıçapı; yalnızca numune yer değiştirmesinin µm değerini etkiler.",
                       "Bragg–Brentano goniometer radius; affects only the specimen displacement in µm."),
    "gui.material": ("Malzeme", "Material"),
    "gui.mat_custom": ("Özel…", "Custom…"),
    "gui.mat_custom_set": ("Özel: a = {a:.4f}, c = {c:.4f} Å", "Custom: a = {a:.4f}, c = {c:.4f} Å"),
    "gui.file_info": ("Seçili dosyanın ölçüm bilgisi…", "Measurement data of the selected file…"),
    "gui.assumed_note": ("{n} dosyada dalga boyu yok; Cu Kα varsayıldı. Gerekirse radyasyonu seçin.",
                         "{n} file(s) contain no wavelength; Cu Kα assumed. Select the radiation if needed."),
    "gui.wizard": ("Adım adım sihirbaz…", "Step-by-step assistant…"),
    "gui.wizard_tip": ("Gerekli bilgileri adım adım sorar (isteğe bağlı).",
                       "Asks for the required data step by step (optional)."),
    "gui.offer_title": ("Analiz", "Analysis"),
    "gui.offer_text": ("Gerekli bilgileri (veri, cihaz, standart malzeme, alaşım) adım adım girmek ister misiniz?",
                       "Would you like to enter the required data (data, instrument, standard material, alloy) "
                       "step by step?"),
    "gui.offer_wizard": ("Sihirbazı aç", "Open the assistant"),
    "gui.offer_direct": ("Doğrudan hesapla", "Run directly"),
    "gui.offer_never": ("Bir daha sorma", "Do not ask again"),

    # dialogs
    "dlg.rad_title": ("Özel radyasyon", "Custom radiation"),
    "dlg.mat_title": ("Özel α-Ti alaşımı", "Custom α-Ti alloy"),
    "dlg.std_title": ("Standart desenden cihaz modeli", "Instrument model from a standard pattern"),
    "dlg.std_file": ("Standart deseni", "Standard pattern"),
    "dlg.browse": ("Seç…", "Browse…"),
    "dlg.none": ("(seçilmedi)", "(none selected)"),

    # standards / materials (labels)
    "std.material": ("Standart malzeme", "Standard material"),
    "std.lattice": ("Kafes parametresi", "Lattice parameter"),
    "std.source": ("Kaynak: {s}", "Source: {s}"),
    "std.other_note": ("İndeksleme ve sıfır kayması yok; bulunan tüm pikler kullanılır.",
                       "No indexing and no zero shift; every peak found is used."),
    "std.degree": ("Polinom derecesi", "Polynomial degree"),
    "std.cert_note": ("Sertifikalı bir standart (ör. NIST SRM) kullanıyorsanız sertifikadaki kafes değerini girin.",
                      "If you use a certified standard (e.g. NIST SRM), enter the lattice value of its certificate."),
    "mat.preset": ("Hazır alaşım", "Preset"),
    "mat.a": ("α a (Å)", "α a (Å)"),
    "mat.c": ("α c (Å)", "α c (Å)"),
    "mat.ab": ("β a (Å)", "β a (Å)"),
    "mat.beta": ("β fazı", "β phase"),
    "mat.beta_auto": ("Otomatik (varsa modelle)", "Automatic (model if present)"),
    "mat.beta_yes": ("Her zaman modelle", "Always model"),
    "mat.beta_no": ("Yok", "None"),
    "mat.refine": ("Nominal kafes desenden belirgin farklıysa otomatik ayarla (önerilir)",
                   "Adjust the nominal lattice automatically when it is clearly off (recommended)"),
    "mat.note": ("Nominal değerler yalnızca pik pencerelerini yerleştirir; kafes parametreleri her numunede "
                 "ölçülür. Kontrast faktörleri ve Burgers vektörleri hcp α/α′ titanyum içindir (Dragomir–Ungár); "
                 "farklı bir hcp metal için geçerli değildir.",
                 "The nominal values only place the peak windows; the lattice parameters are measured for every "
                 "sample. The contrast factors and Burgers vectors are those of hcp α/α′ titanium "
                 "(Dragomir–Ungár) and are not valid for other hcp metals."),

    # wizard
    "wz.title": ("Adım adım dislokasyon yoğunluğu", "Dislocation density step by step"),
    "wz.intro_t": ("Hoş geldiniz", "Welcome"),
    "wz.intro": ("<p>Bu sihirbaz bir analiz için gereken bilgileri sırayla sorar. Her adımda programın "
                 "dosyalardan otomatik okuduğu değerler gösterilir; yalnızca yanlış veya eksik olanları "
                 "değiştirmeniz yeterlidir. Sihirbazı kullanmak zorunlu değildir: aynı ayarlar ana penceredeki "
                 "sol panelde de bulunur.</p><ol><li><b>Veri:</b> numune desenleri ve ölçüm bilgileri "
                 "(radyasyon, Kα2, gonyometre yarıçapı)</li><li><b>Malzeme:</b> titanyum alaşımı ve nominal kafes"
                 "</li><li><b>Cihaz:</b> cihaz genişlemesi için standart malzeme (korundum, LaB₆, Si, CeO₂ veya "
                 "başka)</li><li><b>Seçenekler</b></li><li><b>Özet</b> ve hesaplama</li></ol>",
                 "<p>This assistant asks for the data an analysis needs, one step at a time. Each step shows the "
                 "values the program read from the files automatically; you only change what is wrong or "
                 "missing. Using the assistant is optional: the same settings are in the left panel of the main "
                 "window.</p><ol><li><b>Data:</b> sample patterns and measurement data (radiation, Kα2, "
                 "goniometer radius)</li><li><b>Material:</b> titanium alloy and nominal lattice</li>"
                 "<li><b>Instrument:</b> standard material for the instrumental broadening (corundum, LaB₆, Si, "
                 "CeO₂ or another)</li><li><b>Options</b></li><li><b>Summary</b> and calculation</li></ol>"),
    "wz.offer_check": ("Analizi başlatırken bu sihirbazı öner", "Offer this assistant when an analysis is started"),
    "wz.data_t": ("1 · Veri ve ölçüm bilgileri", "1 · Data and measurement"),
    "wz.data_s": ("Numune desenlerini ekleyin. Dosyadan okunan değerler tabloda; dosyada olmayanlar "
                  "\"varsayıldı\" olarak işaretlenir. Gerekirse aşağıda düzeltin (tüm dosyalara uygulanır).",
                  "Add the sample patterns. Values read from the files are listed; values the file does not "
                  "contain are marked \"assumed\". Correct them below if needed (applies to all files)."),
    "wz.override": ("Düzeltme (dosyadan okunanın yerine)", "Override (instead of the file values)"),
    "wz.col_file": ("Dosya", "File"),
    "wz.mat_t": ("2 · Malzeme", "2 · Material"),
    "wz.mat_s": ("Alaşımı seçin veya nominal kafes parametrelerini girin.",
                 "Select the alloy or enter the nominal lattice parameters."),
    "wz.inst_t": ("3 · Cihaz genişlemesi", "3 · Instrumental broadening"),
    "wz.inst_s": ("Cihaz genişlemesi, aynı difraktometre ve optikle ölçülmüş bir standarttan alınır.",
                  "The instrumental broadening is taken from a standard measured with the same diffractometer "
                  "and optics."),
    "wz.inst_keep": ("Mevcut cihaz modelini kullan", "Use the current instrument model"),
    "wz.inst_load": ("Kayıtlı cihaz modeli yükle (.json)", "Load a saved instrument model (.json)"),
    "wz.inst_build": ("Bir standart ölçümünden yeni model oluştur", "Build a new model from a standard measurement"),
    "wz.fit": ("Standardı uydur", "Fit the standard"),
    "wz.save": ("Modeli kaydet…", "Save model…"),
    "wz.fit_ok": ("{n} pik kullanıldı, K = {k0:.1f}–{k1:.1f} nm⁻¹.", "{n} peaks used, K = {k0:.1f}–{k1:.1f} nm⁻¹."),
    "wz.zero_apply": ("Standardın sıfır kaymasını kafes parametrelerinde düzelt (sertifikalı standartla önerilir)",
                      "Correct the lattice parameters for the zero shift of the standard (recommended with a "
                      "certified standard)"),
    "wz.wl_ok": ("Dalga boyu numunelerle uyumlu.", "Wavelength consistent with the samples."),
    "wz.no_model": ("Henüz cihaz modeli yok.", "No instrument model yet."),
    "wz.opt_t": ("4 · Seçenekler", "4 · Options"),
    "wz.opt_s": ("Varsayılanlar çoğu durumda uygundur.", "The defaults suit most cases."),
    "wz.sum_t": ("5 · Özet", "5 · Summary"),
    "wz.sum_s": ("Ayarları kontrol edin; \"Analizi başlat\" hesaplamayı başlatır.",
                 "Check the settings; \"Run analysis\" starts the calculation."),
    "wz.files": ("Numuneler", "Samples"),
    "wz.instrument": ("Cihaz modeli", "Instrument model"),
    "wz.options": ("Seçenekler", "Options"),
    "wz.yes": ("evet", "yes"),
    "fig.zero_short": ("sıfır kayması {z:+.3f}°", "zero shift {z:+.3f}°"),
    "xl.measurement": ("Ölçüm ve malzeme", "Measurement and material"),
    "xl.file": ("Dosya", "File"),
    "xl.assumed": ("Dosyada yok (varsayıldı)", "Not in the file (assumed)"),
    "xl.material": ("Malzeme", "Material"),
    "xl.nominal": ("Pencere için nominal a, c, β a (Å)", "Nominal a, c, β a for the windows (Å)"),
    "xl.zero_applied": ("Kafes için sıfır kayması (°)", "Zero shift for the lattice (°)"),
    "xl.standard": ("Standart malzeme", "Standard material"),
    "xl.std_lattice": ("Standart kafes (Å)", "Standard lattice (Å)"),
    "xl.wavelength": ("λ₁, λ₂ (Å), Kα2/Kα1", "λ₁, λ₂ (Å), Kα2/Kα1"),
    "xl.zero": ("Sıfır kayması (°)", "Zero shift (°)"),
    "xl.std_disp": ("Standart yer değiştirmesi (µm)", "Standard displacement (µm)"),
    "xl.indexed": ("İndekslenen / bulunan pik", "Peaks indexed / found"),
    "std.name.corundum": ("Korundum α-Al₂O₃ (R-3c)", "Corundum α-Al₂O₃ (R-3c)"),
    "std.name.other": ("diğer / bilinmeyen", "other / unknown"),
    "std.src.corundum": ("nominal (literatür, ör. ICDD PDF 00-046-1212); varsa sertifika değeri",
                         "nominal (literature, e.g. ICDD PDF 00-046-1212); certificate value if available"),
    "std.src.LaB6": ("NIST SRM 660c, 22,5 °C'de sertifikalı", "NIST SRM 660c, certified at 22.5 °C"),
    "std.src.Si": ("NIST SRM 640f, 22,5 °C'de sertifikalı", "NIST SRM 640f, certified at 22.5 °C"),
    "std.src.CeO2": ("nominal (NIST SRM 674a bilgi değeri 5,411102 Å)",
                     "nominal (NIST SRM 674a information value 5.411102 Å)"),
    "mat.name.CP-Ti": ("CP-Ti, derece 1–4 (α)", "CP-Ti, grade 1–4 (α)"),
    "mat.name.custom": ("özel α-Ti alaşımı", "custom α-Ti alloy"),
    "mat.src.Ti-6Al-4V": ("bu çalışmanın nominal değerleri; α′ martensit ve α + β",
                          "nominal values of this work; α′ martensite and α + β"),
    "mat.src.CP-Ti": ("α-Ti, ICDD PDF 00-044-1294; β fazı beklenmez", "α-Ti, ICDD PDF 00-044-1294; no β phase expected"),
    "mat.src.custom": ("kullanıcı değerleri", "user values"),
    "wz.next": ("İleri >", "Next >"),
    "wz.back": ("< Geri", "< Back"),
    "wz.cancel": ("İptal", "Cancel"),
    "dlg.ok": ("Tamam", "OK"),
    "wz.read_error": ("okunamadı: {e}", "cannot be read: {e}"),
    "wz.rad_preset": ("{a} Kα", "{a} Kα"),
    "wz.no": ("hayır", "no"),
})
