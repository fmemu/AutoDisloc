# SPDX-License-Identifier: MIT
# AutoDisloc 2 - Copyright (c) 2026 Firat Memu
"""Text of the AutoDisloc 2 whitepaper in English and Turkish.

build() returns (values, blocks, bib). Markup inside texts: $inline math$,
[@key; @key2] citations, @eq:label / @fig:label / @tab:label / @sec:label
references and «name» placeholders filled from ``values``. Display equations
are language independent.
"""

import numpy as np

from autodisloc.contrast import BURGERS_NM, TI_SUBSYSTEMS, type_parabolas

BIB = {
    "warren1950": "Warren, B.E., Averbach, B.L. (1950). The effect of cold-work distortion on X-ray patterns. "
                  "<i>J. Appl. Phys.</i> 21, 595–599.",
    "warren1969": "Warren, B.E. (1969). <i>X-ray Diffraction</i>. Addison-Wesley, Reading, MA (Dover reprint 1990).",
    "williamson1953": "Williamson, G.K., Hall, W.H. (1953). X-ray line broadening from filed aluminium and wolfram. "
                      "<i>Acta Metall.</i> 1, 22–31.",
    "krivoglaz1996": "Krivoglaz, M.A. (1996). <i>X-ray and Neutron Diffraction in Nonideal Crystals</i>. Springer, Berlin.",
    "wilkens1970": "Wilkens, M. (1970). The determination of density and distribution of dislocations in deformed "
                   "single crystals from broadened X-ray diffraction profiles. <i>Phys. Status Solidi A</i> 2, 359–370.",
    "wilkens1970b": "Wilkens, M. (1970). Theoretical aspects of kinematical X-ray diffraction profiles from crystals "
                    "containing dislocation distributions. In: <i>Fundamental Aspects of Dislocation Theory</i>, "
                    "NBS Spec. Publ. 317, Vol. II, pp. 1195–1221.",
    "ungar1996": "Ungár, T., Borbély, A. (1996). The effect of dislocation contrast on x-ray line broadening: "
                 "a new approach to line profile analysis. <i>Appl. Phys. Lett.</i> 69, 3173–3175.",
    "ungar1999": "Ungár, T., Dragomir, I., Révész, Á., Borbély, A. (1999). The contrast factors of dislocations in "
                 "cubic crystals: the dislocation model of strain anisotropy in practice. <i>J. Appl. Cryst.</i> 32, 992–1002.",
    "ungar2001": "Ungár, T., Gubicza, J., Ribárik, G., Borbély, A. (2001). Crystallite size distribution and "
                 "dislocation structure determined by diffraction profile analysis: principles and practical "
                 "application to cubic and hexagonal crystals. <i>J. Appl. Cryst.</i> 34, 298–310.",
    "ribarik2001": "Ribárik, G., Ungár, T., Gubicza, J. (2001). MWP-fit: a program for multiple whole-profile fitting "
                   "of diffraction peak profiles by ab initio theoretical functions. <i>J. Appl. Cryst.</i> 34, 669–676.",
    "ribarik2004": "Ribárik, G., Gubicza, J., Ungár, T. (2004). Correlation between strength and microstructure of "
                   "ball-milled Al–Mg alloys determined by X-ray diffraction. <i>Mater. Sci. Eng. A</i> 387–389, 343–347.",
    "dragomir2002": "Dragomir, I.C., Ungár, T. (2002). Contrast factors of dislocations in the hexagonal crystal "
                    "system. <i>J. Appl. Cryst.</i> 35, 556–564.",
    "scardi2002": "Scardi, P., Leoni, M. (2002). Whole powder pattern modelling. <i>Acta Cryst. A</i> 58, 190–200.",
    "gubicza2014": "Gubicza, J. (2014). <i>X-Ray Line Profile Analysis in Materials Science</i>. IGI Global, Hershey, PA.",
    "stokes1948": "Stokes, A.R. (1948). A numerical Fourier-analysis method for the correction of widths and shapes "
                  "of lines on X-ray powder photographs. <i>Proc. Phys. Soc.</i> 61, 382–391.",
    "balzar1993": "Balzar, D., Ledbetter, H. (1993). Voigt-function modeling in Fourier analysis of size- and "
                  "strain-broadened X-ray diffraction peaks. <i>J. Appl. Cryst.</i> 26, 97–103.",
    "olivero1977": "Olivero, J.J., Longbothum, R.L. (1977). Empirical fits to the Voigt line width: a brief review. "
                   "<i>J. Quant. Spectrosc. Radiat. Transfer</i> 17, 233–236.",
    "rachinger1948": "Rachinger, W.A. (1948). A correction for the α<sub>1</sub>α<sub>2</sub> doublet in the "
                     "measurement of widths of X-ray diffraction lines. <i>J. Sci. Instrum.</i> 25, 254–255.",
    "hajyakbary2015": "HajyAkbary, F., Sietsma, J., Böttger, A.J., Santofimia, M.J. (2015). An improved X-ray "
                      "diffraction analysis method to characterize dislocation density in lath martensitic "
                      "structures. <i>Mater. Sci. Eng. A</i> 639, 208–218.",
    "muiruri2020": "Muiruri, A., Maringa, M., du Preez, W. (2020). Evaluation of dislocation densities in various "
                   "microstructures of additively manufactured Ti6Al4V (Eli) by the method of X-ray diffraction. "
                   "<i>Materials</i> 13, 5355. doi:10.3390/ma13235355",
    "shintani2010": "Shintani, T., Murata, Y., Terada, Y., Morinaga, M. (2010). Evaluation of dislocation density in "
                    "a Mg–Al–Mn–Ca alloy determined by X-ray diffractometry and transmission electron microscopy. "
                    "<i>Mater. Trans.</i> 51, 1067–1071. doi:10.2320/matertrans.M2010021",
    "cong2011": "Cong, Z., Murata, Y. (2011). Dislocation density of lath martensite in 10Cr-5W heat-resistant "
                "steels. <i>Mater. Trans.</i> 52, 2151–2154. doi:10.2320/matertrans.M2011201",
    "cottam2019": "Cottam, R., Palanisamy, S., Avdeev, M., Jarvis, T., Henry, C., Cuiuri, D., Balogh, L., "
                  "Rahman Rashid, R.A. (2019). Diffraction line profile analysis of 3D wedge samples of Ti-6Al-4V "
                  "fabricated using four different additive manufacturing processes. <i>Metals</i> 9, 60. "
                  "doi:10.3390/met9010060",
    "harris1952": "Harris, G.B. (1952). Quantitative measurement of preferred orientation in rolled uranium bars. "
                  "<i>Phil. Mag.</i> 43, 113–123.",
    "wilks1938": "Wilks, S.S. (1938). The large-sample distribution of the likelihood ratio for testing composite "
                 "hypotheses. <i>Ann. Math. Statist.</i> 9, 60–62.",
    "lawson1974": "Lawson, C.L., Hanson, R.J. (1974). <i>Solving Least Squares Problems</i>. Prentice-Hall, "
                  "Englewood Cliffs, NJ.",
    "branch1999": "Branch, M.A., Coleman, T.F., Li, Y. (1999). A subspace, interior, and conjugate gradient method "
                  "for large-scale bound-constrained minimization problems. <i>SIAM J. Sci. Comput.</i> 21, 1–23.",
    "virtanen2020": "Virtanen, P. et al. (2020). SciPy 1.0: fundamental algorithms for scientific computing in "
                    "Python. <i>Nat. Methods</i> 17, 261–272.",
    "abramowitz1964": "Abramowitz, M., Stegun, I.A. (1964). <i>Handbook of Mathematical Functions</i>. "
                      "National Bureau of Standards, Applied Mathematics Series 55.",
    "cohen1935": "Cohen, M.U. (1935). Precision lattice constants from X-ray powder photographs. "
                 "<i>Rev. Sci. Instrum.</i> 6, 68–74.",
    "black2020": "Black, D.R., Mendenhall, M.H., Henins, A., Filliben, J., Cline, J.P. (2020). Certification of "
                 "Standard Reference Material 660c for powder diffraction. <i>Powder Diffr.</i> 35, 17–22.",
    "nist640f": "National Institute of Standards and Technology. Certificate of Analysis, Standard Reference "
                "Material 640f: Line Position and Line Shape Standard for Powder Diffraction (Silicon Powder). "
                "Gaithersburg, MD. tsapps.nist.gov/srmext/certificates/archives/640f.pdf",
    "prince2004": "Prince, E. (ed.) (2004). <i>International Tables for Crystallography, Vol. C: Mathematical, "
                  "Physical and Chemical Tables</i>, 3rd ed. Kluwer, Dordrecht.",
    "taylor1934": "Taylor, G.I. (1934). The mechanism of plastic deformation of crystals. Part I. Theoretical. "
                  "<i>Proc. R. Soc. Lond. A</i> 145, 362–387.",
}


def sci(v, d=2):
    if v is None or not np.isfinite(v):
        return "–"
    if v == 0:
        return "0"
    e = int(np.floor(np.log10(abs(v))))
    return f"{v / 10 ** e:.{d}f}×10<sup>{e}</sup>"


def num(v, f="{:.2f}"):
    return "–" if v is None or not np.isfinite(v) else f.format(v)


def _lat(res):
    """Lattice parameters (computed here for results cached before they existed)."""
    lat = getattr(res, "lattice", None)
    if not lat:
        from autodisloc.pipeline import AnalysisOptions, beta_for_lattice, phase_lattice
        lat = phase_lattice(res.alpha_fits, beta_for_lattice(res.pattern, AnalysisOptions(), []), res.pattern)
        res.lattice = lat
    return lat


def _std(inst):
    """Indexing and zero shift of the instrument standard (placeholders std_*)."""
    from autodisloc import standards
    pts = getattr(inst, "points", None) or {}
    if not getattr(inst, "n_indexed", None) or not inst.wavelength or "two_theta" not in pts:
        return {"std_n": "–", "std_rms": "–", "std_z": "–", "std_s": "–"}
    tt = pts["two_theta"]
    _, calc = standards.index_peaks(tt, inst.standard, inst.wavelength[0], inst.lattice.get("a"),
                                    inst.lattice.get("c"))
    zs = standards.zero_shift(tt, calc, inst.radius_mm or 250.0)
    return {"std_n": f"{inst.n_indexed}/{inst.n_found}", "std_rms": f"{zs['rms_deg']:.3f}",
            "std_z": f"{zs['zero_deg']:+.3f} ± {zs['zero_err_deg']:.3f}",
            "std_s": f"{zs['disp_um']:.0f} ± {zs['disp_err_um']:.0f}"}


def build(lang, data, figs, inst):
    E = lang == "en"
    t = lambda en, tr: en if E else tr
    B = []

    def H(level, label, en, tr, numbered=True):
        B.append(["h", level, label, t(en, tr), numbered])

    def P(en, tr):
        B.append(["p", t(en, tr)])

    def NOTE(en, tr, css="note"):
        B.append(["note", t(en, tr), css])

    def EX(en, tr):
        B.append(["note", f'<b class="lbl">{t("Worked example.", "Uygulamalı örnek.")}</b> ' + t(en, tr), "example"])

    def UL(en, tr, ordered=False):
        B.append(["ul", t(en, tr), ordered])

    def EQ(label, tex):
        B.append(["eq", label, tex])

    def FIG(label, key, en, tr, width=1.0):
        B.append(["fig", label, figs[key], t(en, tr), width])

    def TAB(label, en, tr, head, rows, css=""):
        B.append(["tab", label, t(en, tr), head, rows, css])

    # ------------------------------------------------------------------ values
    res = data["results"]
    ex, up = res[0], res[-1]
    synthetic = data["example"] == "synthetic"
    w, m, p = ex.wp, ex.mwh, ex.population
    truth = data["truth"].get(ex.sample, {})
    P_t, T1, T2 = type_parabolas()
    tl = {"a": "⟨a⟩", "c": "⟨c⟩", "c+a": "⟨c+a⟩"}
    V = {
        "ex": ex.sample, "up": up.sample,
        "rho": sci(w.rho), "lo": sci(ex.wp_interval[0], 1), "hi": sci(ex.wp_interval[1], 1),
        "Mstar": f"{w.M_star:.2f}", "Restar": f"{w.Re_star_nm:.0f}", "ha": f"{w.h['a']:.2f}",
        "hc": f"{w.h['c']:.2f}", "hca": f"{w.h['c+a']:.2f}", "b2c": f"{w.b2c_hk0:.4f}",
        "m_nm": f"{w.m_nm:.0f}", "sig": f"{w.sigma:.2f}", "rwp": f"{w.rwp:.1f}",
        "gof": f"{w.params['chi2'] / w.params['dof']:.2f}", "npts": f"{w.params['n_points']}",
        "dof": f"{w.params['dof']}", "nfree": f"{w.params['n_points'] - w.params['dof']}",
        "alpha": sci(m.alpha, 2), "beta": sci(m.beta, 2), "q1": f"{m.q1:.3f}", "q2": f"{m.q2:.3f}",
        "D": f"{m.D_nm:.0f}" if np.isfinite(m.D_nm) else "∞", "mwh_r2": f"{m.r2:.3f}",
        "qf1": f"{ex.mwh_free.q1:.2f}", "qf2": f"{ex.mwh_free.q2:.2f}",
        "pha": f"{p.h['a']:.2f}", "phc": f"{p.h['c']:.2f}", "phca": f"{p.h['c+a']:.2f}", "pb2c": f"{p.b2c_hk0:.4f}",
        "pb2cmin": f"{p.b2c_min:.4f}", "pb2cmax": f"{p.b2c_max:.4f}",
        "mwa_rho": sci(ex.mwa.rho) if ex.valid else "–", "mwa_L": f"{ex.mwa.L.min():.0f}–{ex.mwa.L.max():.0f}",
        "mwa_Re": f"{ex.mwa.Re_nm:.0f}" if np.isfinite(ex.mwa.Re_nm) else "–",
        "a_A": f"{_lat(ex)['a']:.4f}", "c_A": f"{_lat(ex)['c']:.4f}", "disp": f"{_lat(ex)['disp_um']:.0f}",
        **_std(inst),
        "inst_g": ", ".join(f"{v:.3e}" for v in inst.gauss_coef),
        "inst_l": ", ".join(f"{v:.3e}" for v in inst.lorentz_coef),
        "upper": sci(up.wp_interval[1], 1), "kmin": f"{inst.k_range[0]:.1f}", "kmax": f"{inst.k_range[1]:.1f}",
        "comb_n": f"{ex.combos['n'] if ex.combos else 0}",
        "interval_method": str(ex.wp_interval_method),
    }
    if synthetic:
        V.update({"t_rho": sci(truth["rho_m-2"]), "t_M": f"{truth['M_star']:.2f}", "t_ha": f"{truth['h_a']:.2f}",
                  "t_m": f"{truth['size_median_nm']:.0f}", "t_sig": f"{truth['size_sigma']:.2f}",
                  "t_q1": f"{truth['q1']:.3f}", "t_q2": f"{truth['q2']:.3f}"})
        exdesc = t("synthetic pattern A of <code>examples/</code> (true ρ = «t_rho» m<sup>−2</sup>, M* = «t_M», "
                   "h⟨a⟩ = «t_ha», size median «t_m» nm), generated with the model of @sec:wp, the example "
                   "instrument model, Cu Kα1+Kα2 and Poisson noise",
                   "<code>examples/</code> klasöründeki sentetik A deseni (gerçek ρ = «t_rho» m<sup>−2</sup>, "
                   "M* = «t_M», h⟨a⟩ = «t_ha», boyut medyanı «t_m» nm); @sec:wp'deki modelle, örnek cihaz modeli, "
                   "Cu Kα1+Kα2 ve Poisson gürültüsüyle üretildi")
    else:
        exdesc = t("the measured sample «ex»", "ölçülmüş «ex» numunesi")
    V["exdesc"] = exdesc.replace("«t_rho»", V.get("t_rho", "")).replace("«t_M»", V.get("t_M", "")) \
        .replace("«t_ha»", V.get("t_ha", "")).replace("«t_m»", V.get("t_m", "")).replace("«ex»", V["ex"])

    V["abstract"] = t(
        "AutoDisloc 2 determines the dislocation density ρ, the Burgers-vector population and the dislocation "
        "arrangement parameter M* of hcp α/α′ Ti-6Al-4V from laboratory X-ray diffraction patterns. This document "
        "derives every step of the calculation from its physical starting point: the Fourier description of a "
        "diffraction profile, the Krivoglaz–Wilkens theory of strain broadening by dislocations, the "
        "Dragomir–Ungár contrast factors of hexagonal crystals, the modified Williamson–Hall (mWH) and modified "
        "Warren–Averbach (mWA) methods, and the Wilkens whole-profile fit that gives the main result. Each step is "
        "illustrated on a worked example, «exdesc». For this example the program finds ρ = «rho» m<sup>−2</sup> "
        "(95 % interval «lo»–«hi»), M* = «Mstar» and an ⟨a⟩ fraction of «ha»; the model explains the "
        "«npts» data points with χ²/ν = «gof». The document also explains two errors found in the literature "
        "(a factor of 2 in ΔK and an incorrect Voigt Fourier transform), gives the uncertainty and detection-limit "
        "procedures, and reports the validation against published numbers and synthetic data.",
        "AutoDisloc 2, laboratuvar X-ışını kırınım desenlerinden hcp α/α′ Ti-6Al-4V'nin dislokasyon yoğunluğunu "
        "(ρ), Burgers vektörü popülasyonunu ve dislokasyon düzen parametresini (M*) hesaplar. Bu doküman hesabın "
        "her adımını fiziksel çıkış noktasından türetir: kırınım profilinin Fourier gösterimi, dislokasyonların "
        "neden olduğu gerinim genişlemesinin Krivoglaz–Wilkens kuramı, hekzagonal kristallerin Dragomir–Ungár "
        "kontrast faktörleri, modifiye Williamson–Hall (mWH) ve modifiye Warren–Averbach (mWA) yöntemleri ve ana "
        "sonucu veren Wilkens tam profil uydurması. Her adım uygulamalı bir örnek üzerinde gösterilir: «exdesc». "
        "Bu örnek için program ρ = «rho» m<sup>−2</sup> (%95 aralık «lo»–«hi»), M* = «Mstar» ve ⟨a⟩ oranı «ha» "
        "buluyor; model «npts» veri noktasını χ²/ν = «gof» ile açıklıyor. Doküman ayrıca literatürde bulunan iki "
        "hatayı (ΔK'de 2 çarpanı ve hatalı bir Voigt Fourier dönüşümü) açıklar, belirsizlik ve algılama sınırı "
        "yöntemlerini verir ve yayımlanmış sayılarla ve sentetik veriyle yapılan doğrulamayı raporlar.")
    V["keywords"] = t("<b>Keywords:</b> X-ray line profile analysis; dislocation density; contrast factor; "
                      "Wilkens model; modified Williamson–Hall; modified Warren–Averbach; whole-profile fitting; "
                      "Ti-6Al-4V; additive manufacturing",
                      "<b>Anahtar kelimeler:</b> X-ışını çizgi profili analizi; dislokasyon yoğunluğu; kontrast "
                      "faktörü; Wilkens modeli; modifiye Williamson–Hall; modifiye Warren–Averbach; tam profil "
                      "uydurması; Ti-6Al-4V; eklemeli imalat")

    # =================================================================== NOMENCLATURE
    H(1, "nomenclature", "Nomenclature, abbreviations and terms", "Semboller, kısaltmalar ve terimler", numbered=False)
    sym = [
        ("$\\lambda_1,\\ \\lambda_2$", t("Cu Kα1 and Kα2 wavelengths (0.1540598, 0.1544426)", "Cu Kα1 ve Kα2 dalga boyları (0,1540598, 0,1544426)"), "nm"),
        ("$\\theta,\\ 2\\theta$", t("Bragg angle, diffraction angle", "Bragg açısı, kırınım açısı"), "°, rad"),
        ("$d$", t("lattice-plane spacing", "düzlemler arası uzaklık"), "nm"),
        ("$K=2\\sin\\theta/\\lambda$", t("magnitude of the diffraction vector (= 1/d at the Bragg position); also written g", "kırınım vektörünün büyüklüğü (Bragg konumunda = 1/d); g olarak da yazılır"), "nm⁻¹"),
        ("$\\Delta K$", t("full width at half maximum (FWHM) in K units", "K biriminde yarı yükseklikteki tam genişlik (FWHM)"), "nm⁻¹"),
        ("$s$", t("distance from the peak centre in K units", "pik merkezinden K birimindeki uzaklık"), "nm⁻¹"),
        ("$w_G,\\ w_L$", t("Gaussian and Lorentzian component FWHMs of a Voigt profile", "Voigt profilinin Gauss ve Lorentz bileşen FWHM'leri"), "nm⁻¹ / °"),
        ("$L$", t("Fourier length (distance between scattering cells along the diffraction vector)", "Fourier uzunluğu (kırınım vektörü yönünde saçıcı hücreler arası uzaklık)"), "nm"),
        ("$A(L)$", t("cosine Fourier coefficient of a profile, A(0) = 1", "profilin kosinüs Fourier katsayısı, A(0) = 1"), "–"),
        ("$A^S,\\ A^D,\\ A^I$", t("size, dislocation (distortion) and instrumental Fourier coefficients", "boyut, dislokasyon (bozulma) ve cihaz Fourier katsayıları"), "–"),
        ("$\\rho$", t("dislocation density (line length per volume)", "dislokasyon yoğunluğu (birim hacimdeki çizgi uzunluğu)"), "m⁻²"),
        ("$b$", t("magnitude of the Burgers vector (⟨a⟩ 0.295, ⟨c⟩ 0.468, ⟨c+a⟩ 0.553)", "Burgers vektörünün büyüklüğü (⟨a⟩ 0,295, ⟨c⟩ 0,468, ⟨c+a⟩ 0,553)"), "nm"),
        ("$C,\\ \\overline{C}_{hkl}$", t("dislocation contrast factor; its average over the slip systems for reflection hkl", "dislokasyon kontrast faktörü; hkl yansıması için kayma sistemleri üzerinden ortalaması"), "–"),
        ("$\\overline{b^2C}_{hk.0}$", t("average b²C of the hk.0 reflections of a dislocation population", "bir dislokasyon popülasyonunun hk.0 yansımaları için ortalama b²C değeri"), "nm²"),
        ("$q_1,\\ q_2$", t("parameters of the l-dependence of the hexagonal contrast factor", "hekzagonal kontrast faktörünün l'ye bağlılık parametreleri"), "–"),
        ("$x=\\frac{2}{3}(l/Ka)^2$", t("hexagonal contrast variable", "hekzagonal kontrast değişkeni"), "–"),
        ("$a,\\ c$", t("hexagonal lattice parameters", "hekzagonal kafes parametreleri"), "nm, Å"),
        ("$h_t$", t("fraction of dislocations of Burgers type t ∈ {⟨a⟩, ⟨c⟩, ⟨c+a⟩}, Σh = 1", "Burgers tipi t ∈ {⟨a⟩, ⟨c⟩, ⟨c+a⟩} olan dislokasyonların oranı, Σh = 1"), "–"),
        ("$P_t,\\ q_j^{t}$", t("type-averaged b²C̄ and q parameters of Burgers type t", "Burgers tipi t'nin tip ortalamalı b²C̄ ve q parametreleri"), "nm², –"),
        ("$R_e,\\ R_e^*$", t("effective outer cut-off radius of the dislocations: R_e of the ln(R_e/L) form, R_e* = R_e/2.877 (program convention; CMWP R_e* = R_e*/2.568, @sec:ffunc)", "dislokasyonların etkin dış kesme yarıçapı: ln(R_e/L) biçimindeki R_e, R_e* = R_e/2,877 (programın tanımı; CMWP R_e* = R_e*/2,568, @sec:ffunc)"), "nm"),
        ("$M^*=R_e^*\\sqrt{\\rho}$", t("dislocation arrangement parameter (program convention; CMWP M* = M*/2.568, @sec:ffunc)", "dislokasyon düzen parametresi (programın tanımı; CMWP M* = M*/2,568, @sec:ffunc)"), "–"),
        ("$\\eta,\\ f(\\eta)$", t("reduced Fourier length L/R_e* (program convention); Wilkens function", "indirgenmiş Fourier uzunluğu L/R_e* (programın tanımı); Wilkens fonksiyonu"), "–"),
        ("$\\langle\\varepsilon^2_{g,L}\\rangle$", t("mean-square strain over the distance L along g", "g yönünde L uzaklığı üzerinden ortalama kare gerinim"), "–"),
        ("$D,\\ m,\\ \\sigma$", t("crystallite diameter; median and log-standard deviation of its log-normal distribution", "kristalit çapı; log-normal dağılımının medyanı ve logaritmik standart sapması"), "nm, nm, –"),
        ("$\\alpha,\\ \\beta$", t("size and strain coefficients of the mWH equation", "mWH denkleminin boyut ve gerinim katsayıları"), "nm⁻²"),
        ("$Y(L),\\ s$", t("slope of ln A(L) vs K²b²C̄; slope of Y/L² vs ln L in the mWA", "ln A(L)'nin K²b²C̄'ye göre eğimi; mWA'da Y/L²'nin ln L'ye göre eğimi"), "nm², nm⁻²"),
        ("$\\chi^2,\\ \\nu$", t("weighted sum of squared residuals; degrees of freedom", "ağırlıklı artık kareler toplamı; serbestlik derecesi"), "–"),
        ("$T_{hkl}$", t("Harris texture index", "Harris doku katsayısı"), "–"),
    ]
    TAB("sym", "Symbols. Units are those used in the program unless stated otherwise.",
        "Semboller. Aksi belirtilmedikçe birimler programda kullanılanlardır.",
        [t("Symbol", "Sembol"), t("Meaning", "Anlamı"), t("Unit", "Birim")], sym, "sym")
    abbr = [
        ("XRD", t("X-ray diffraction", "X-ışını kırınımı")),
        ("XLPA", t("X-ray line profile analysis", "X-ışını çizgi profili analizi")),
        ("FWHM", t("full width at half maximum", "yarı yükseklikteki tam genişlik")),
        ("WH / mWH", t("Williamson–Hall / modified Williamson–Hall method", "Williamson–Hall / modifiye Williamson–Hall yöntemi")),
        ("WA / mWA", t("Warren–Averbach / modified Warren–Averbach method", "Warren–Averbach / modifiye Warren–Averbach yöntemi")),
        ("CMWP, eCMWP", t("convolutional multiple whole profile fitting (extended); program of Ribárik and Ungár", "konvolüsyonlu çoklu tam profil uydurması (genişletilmiş); Ribárik ve Ungár'ın programı")),
        ("MWP", t("multiple whole profile fitting", "çoklu tam profil uydurması")),
        ("WPPM", t("whole powder pattern modelling", "tüm toz deseni modellemesi")),
        ("hcp, bcc", t("hexagonal close-packed, body-centred cubic", "sıkı paket hekzagonal, hacim merkezli kübik")),
        ("α, α′, β", t("hcp α phase, hcp martensite, bcc β phase of Ti-6Al-4V", "Ti-6Al-4V'nin hcp α fazı, hcp martensit, hacim merkezli kübik β fazı")),
        ("LPBF, SLM, DMLS", t("laser powder-bed fusion and its trade names (selective laser melting, direct metal laser sintering)", "lazer toz yatağı füzyonu ve ticari adları (seçici lazer ergitme, doğrudan metal lazer sinterleme)")),
        ("AB", t("as-built (not heat treated)", "üretildiği gibi (ısıl işlemsiz)")),
        ("ECAP", t("equal-channel angular pressing", "eşit kanal açısal presleme")),
        ("EBSD", t("electron backscatter diffraction", "geri saçılan elektron kırınımı")),
        ("ICDD", t("International Centre for Diffraction Data (powder reference intensities)", "Uluslararası Kırınım Verileri Merkezi (toz referans şiddetleri)")),
        ("SRM, NIST", t("standard reference material of the US National Institute of Standards and Technology", "ABD Ulusal Standartlar ve Teknoloji Enstitüsü'nün standart referans malzemesi")),
        ("NNLS", t("non-negative least squares", "negatif olmayan en küçük kareler")),
        ("LP", t("linear programming", "doğrusal programlama")),
        ("TRF", t("trust-region reflective least-squares algorithm", "güven bölgesi yansıtmalı en küçük kareler algoritması")),
        ("MC", t("Monte Carlo", "Monte Carlo")),
        ("Rwp", t("weighted profile R factor", "ağırlıklı profil R faktörü")),
    ]
    TAB("abbr", "Abbreviations.", "Kısaltmalar.", [t("Abbreviation", "Kısaltma"), t("Meaning", "Anlamı")], abbr, "abbr")
    gloss = [
        (t("Burgers vector", "Burgers vektörü"), t("the lattice translation that measures the closure failure of a circuit around a dislocation; its magnitude b sets the strength of the strain field", "dislokasyon etrafındaki bir devrenin kapanma hatasını ölçen kafes ötelemesi; büyüklüğü b, gerinim alanının şiddetini belirler")),
        (t("Slip system / sub-slip-system", "Kayma sistemi / alt kayma sistemi"), t("a slip plane with a slip direction; Dragomir and Ungár divide each hcp slip system further by dislocation character (edge or screw) into the 11 sub-systems of @tab:sub", "bir kayma düzlemi ve kayma yönü; Dragomir ve Ungár her hcp kayma sistemini dislokasyon karakterine (kenar veya vida) göre @tab:sub'deki 11 alt sisteme ayırır")),
        (t("Contrast factor", "Kontrast faktörü"), t("dimensionless factor that measures how visible a dislocation is in a given reflection; it depends on the angles between the diffraction vector, the Burgers vector and the line direction and on the elastic constants", "bir dislokasyonun belirli bir yansımada ne kadar görünür olduğunu ölçen boyutsuz faktör; kırınım vektörü, Burgers vektörü ve çizgi yönü arasındaki açılara ve elastik sabitlere bağlıdır")),
        (t("Burgers-vector population", "Burgers vektörü popülasyonu"), t("fractions h of the dislocation density carried by ⟨a⟩, ⟨c⟩ and ⟨c+a⟩ dislocations", "dislokasyon yoğunluğunun ⟨a⟩, ⟨c⟩ ve ⟨c+a⟩ dislokasyonlarınca taşınan kesirleri h")),
        (t("Attainable region", "Ulaşılabilir bölge"), t("set of (q₁, q₂) pairs that some mixture of Ti sub-slip-systems can produce; the convex hull of the sub-system points (@sec:mixture)", "bir Ti alt kayma sistemi karışımının üretebildiği (q₁, q₂) çiftleri kümesi; alt sistem noktalarının dışbükey zarfı (@sec:mixture)")),
        (t("Crystallite (coherent domain)", "Kristalit (koherent bölge)"), t("region that scatters coherently; smaller than or equal to the grain", "eş evreli saçılma yapan bölge; tanecikten küçük veya ona eşit")),
        (t("Fourier length L", "Fourier uzunluğu L"), t("conjugate variable of s; distance between pairs of unit cells measured along the diffraction vector (@sec:L)", "s'nin eşlenik değişkeni; kırınım vektörü boyunca ölçülen birim hücre çiftleri arası uzaklık (@sec:L)")),
        (t("Outer cut-off radius", "Dış kesme yarıçapı"), t("distance beyond which the strain fields of the dislocations screen each other", "dislokasyonların gerinim alanlarının birbirini perdelediği uzaklık")),
        (t("Arrangement parameter M*", "Düzen parametresi M*"), t("R_e*√ρ (program convention, @sec:ffunc): small values mean strongly screened (e.g. dipolar) arrangements, large values weakly correlated dislocations", "R_e*√ρ (programın tanımı, @sec:ffunc): küçük değerler güçlü perdelenmiş (ör. dipol) düzenleri, büyük değerler zayıf ilişkili dislokasyonları gösterir")),
        (t("Instrumental profile", "Cihaz profili"), t("profile that the diffractometer gives for a sample without size or strain broadening; measured on a line standard", "boyut ve gerinim genişlemesi olmayan bir numune için difraktometrenin verdiği profil; çizgi standardında ölçülür")),
        (t("Line standard", "Çizgi standardı"), t("well-crystallised powder with negligible physical broadening (e.g. LaB6 SRM 660, Si, corundum)", "fiziksel genişlemesi ihmal edilebilir, iyi kristallenmiş toz (ör. LaB6 SRM 660, Si, korundum)")),
        (t("Kα doublet; Kα2 stripping", "Kα ikilisi; Kα2 ayıklama"), t("the Cu Kα radiation consists of two lines (Kα1, Kα2); stripping is the numerical removal of the Kα2 part (@sec:strip)", "Cu Kα ışınımı iki çizgiden oluşur (Kα1, Kα2); ayıklama Kα2 kısmının sayısal olarak çıkarılmasıdır (@sec:strip)")),
        (t("Detection limit", "Algılama sınırı"), t("dislocation density below which the dislocation broadening cannot be distinguished from the instrumental and size broadening", "altında dislokasyon genişlemesinin cihaz ve boyut genişlemesinden ayırt edilemediği dislokasyon yoğunluğu")),
        (t("Profile likelihood", "Profil olabilirliği"), t("χ² as a function of one parameter, minimised over all others; used for confidence limits (@sec:pl)", "diğer tüm parametreler üzerinden minimize edilmiş, tek bir parametrenin fonksiyonu olarak χ²; güven sınırları için kullanılır (@sec:pl)")),
    ]
    TAB("gloss", "Terms.", "Terimler.", [t("Term", "Terim"), t("Definition", "Tanım")], gloss, "gloss")

    # =================================================================== 1 INTRODUCTION
    B.append(["pagebreak"])
    H(1, "intro", "Introduction", "Giriş")
    H(2, "motivation", "Why the dislocation density, and why X-rays", "Neden dislokasyon yoğunluğu, neden X-ışınları")
    P("Dislocations carry plastic deformation, and their density ρ controls the work hardening of a metal: in the "
      "Taylor relation the flow-stress contribution grows as $\\sqrt{\\rho}$ [@taylor1934]. In Ti-6Al-4V made by "
      "laser powder-bed fusion (LPBF) the rapid cooling produces α′ martensite with a high dislocation density, "
      "and post-build heat treatments remove most of it. Measuring ρ before and after such treatments is therefore "
      "a central part of linking processing, microstructure and properties.",
      "Dislokasyonlar plastik deformasyonu taşır ve yoğunlukları ρ bir metalin pekleşmesini belirler: Taylor "
      "bağıntısında akma gerilmesine katkı $\\sqrt{\\rho}$ ile artar [@taylor1934]. Lazer toz yatağı füzyonuyla "
      "(LPBF) üretilen Ti-6Al-4V'de hızlı soğuma, yüksek dislokasyon yoğunluklu α′ martensit oluşturur; üretim "
      "sonrası ısıl işlemler bunun büyük kısmını giderir. Bu nedenle ρ'yu ısıl işlemden önce ve sonra ölçmek, "
      "üretim, mikroyapı ve özellikler arasındaki ilişkiyi kurmanın temel bir parçasıdır.")
    P("Every dislocation distorts the lattice around it. The distortion makes the lattice-plane spacing vary from "
      "place to place, so that a reflection is diffracted over a range of angles instead of at one Bragg angle: the "
      "peak broadens. Because the X-ray beam samples about 10<sup>9</sup>–10<sup>11</sup> µm³ of material, the "
      "broadening gives a volume-averaged ρ that complements the local view of transmission electron microscopy. "
      "Small crystallites broaden the peaks as well, and so does the diffractometer itself; the analysis must "
      "separate the three contributions.",
      "Her dislokasyon çevresindeki kafesi bozar. Bozulma düzlemler arası uzaklığı yerden yere değiştirir; bu yüzden "
      "bir yansıma tek bir Bragg açısında değil bir açı aralığında kırınıma uğrar, yani pik genişler. X-ışını demeti "
      "yaklaşık 10<sup>9</sup>–10<sup>11</sup> µm³ malzemeyi örneklediği için genişleme, geçirimli elektron "
      "mikroskobunun yerel bakışını tamamlayan hacim ortalamalı bir ρ verir. Küçük kristalitler de pikleri "
      "genişletir, difraktometrenin kendisi de; analiz bu üç katkıyı birbirinden ayırmalıdır.")
    H(2, "methods", "Line profile analysis methods", "Çizgi profili analizi yöntemleri")
    P("The classical Williamson–Hall (WH) method [@williamson1953] separates size and strain through the different "
      "dependence of the peak width on the diffraction vector K, and the Warren–Averbach (WA) method [@warren1950; "
      "@warren1969] does the same with the Fourier coefficients of the profiles. Both assume that the strain is "
      "isotropic. Dislocation strain is not: a dislocation is invisible in reflections for which its displacement "
      "field has no component along the diffraction vector. Ungár and Borbély [@ungar1996] introduced the "
      "dislocation contrast factor C into both methods, which turned them into the modified Williamson–Hall (mWH) "
      "and modified Warren–Averbach (mWA) methods. Dragomir and Ungár [@dragomir2002] worked out the contrast "
      "factors of hexagonal crystals and showed how the Burgers-vector population follows from them.",
      "Klasik Williamson–Hall (WH) yöntemi [@williamson1953] boyutu ve gerinimi, pik genişliğinin kırınım vektörü "
      "K'ye farklı bağlılığından ayırır; Warren–Averbach (WA) yöntemi [@warren1950; @warren1969] aynı ayrımı "
      "profillerin Fourier katsayılarıyla yapar. İkisi de gerinimin izotrop olduğunu varsayar. Dislokasyon gerinimi "
      "izotrop değildir: yer değiştirme alanının kırınım vektörü yönünde bileşeni olmayan yansımalarda dislokasyon "
      "görünmez. Ungár ve Borbély [@ungar1996] dislokasyon kontrast faktörü C'yi iki yönteme de ekleyerek modifiye "
      "Williamson–Hall (mWH) ve modifiye Warren–Averbach (mWA) yöntemlerini oluşturdu. Dragomir ve Ungár "
      "[@dragomir2002] hekzagonal kristallerin kontrast faktörlerini hesapladı ve Burgers vektörü popülasyonunun "
      "bunlardan nasıl çıkarılacağını gösterdi.")
    P("The whole-profile methods go one step further and fit physical models of the size and strain Fourier "
      "coefficients directly to the measured intensities of all reflections at once: MWP and CMWP of Ribárik, "
      "Ungár and co-workers [@ungar2001; @ribarik2001; @ribarik2004] and the WPPM of Scardi and Leoni "
      "[@scardi2002]. They avoid the intermediate step of extracting a width or a Fourier coefficient for every "
      "peak, which is where most of the instability of the mWH/mWA chain comes from [@gubicza2014].",
      "Tam profil yöntemleri bir adım daha ileri gider ve boyut ve gerinim Fourier katsayılarının fiziksel "
      "modellerini tüm yansımaların ölçülen şiddetlerine aynı anda doğrudan uydurur: Ribárik, Ungár ve "
      "çalışma arkadaşlarının MWP ve CMWP programları [@ungar2001; @ribarik2001; @ribarik2004] ve Scardi ile "
      "Leoni'nin WPPM yöntemi [@scardi2002]. Bu yöntemler her pik için bir genişlik ya da Fourier katsayısı çıkarma "
      "ara adımından kaçınır; mWH/mWA zincirindeki kararsızlığın çoğu bu adımdan kaynaklanır [@gubicza2014].")
    H(2, "scope", "What AutoDisloc does", "AutoDisloc ne yapar")
    P("AutoDisloc combines the methods in one chain (@fig:pipeline). The peaks are fitted as Kα1/Kα2 Voigt doublets "
      "(@sec:peaks) and corrected for the instrument (@sec:instrument). The constrained mWH (@sec:mwh) gives the "
      "reflection dependence of the contrast factor and the Burgers-vector population (@sec:burgers). The main "
      "result comes from the Wilkens whole-profile fit (@sec:wp) with its uncertainty (@sec:unc). The Voigt-based "
      "mWA of the earlier literature (@sec:mwa) is computed for comparison. The theory behind these steps is set out "
      "in @sec:diffraction, @sec:theory and @sec:contrast.",
      "AutoDisloc bu yöntemleri tek bir zincirde birleştirir (@fig:pipeline). Pikler Kα1/Kα2 Voigt ikilileri olarak "
      "uydurulur (@sec:peaks) ve cihaz katkısından arındırılır (@sec:instrument). Kısıtlı mWH (@sec:mwh), kontrast "
      "faktörünün yansımaya bağlılığını ve Burgers vektörü popülasyonunu verir (@sec:burgers). Ana sonuç, "
      "belirsizliğiyle birlikte (@sec:unc) Wilkens tam profil uydurmasından gelir (@sec:wp). Önceki literatürün "
      "Voigt tabanlı mWA'sı karşılaştırma için hesaplanır (@sec:mwa). Bu adımların arkasındaki kuram @sec:diffraction, "
      "@sec:theory ve @sec:contrast'ta verilmiştir.")
    FIG("pipeline", "pipeline", "Analysis chain of AutoDisloc 2. The blue path gives the main result; the orange path "
        "(Voigt-based mWA) is the approach of refs. [@hajyakbary2015; @muiruri2020] with corrected constants and is "
        "reported for comparison.",
        "AutoDisloc 2'nin analiz zinciri. Mavi yol ana sonucu verir; turuncu yol (Voigt tabanlı mWA) "
        "[@hajyakbary2015; @muiruri2020] kaynaklarının yaklaşımının sabitleri düzeltilmiş hâlidir ve karşılaştırma "
        "için raporlanır.")
    P("The worked example of this document is «exdesc». Green boxes show the numbers that the program computes for "
      "it at each step.",
      "Bu dokümanın uygulamalı örneği «exdesc». Yeşil kutular programın her adımda bu örnek için hesapladığı "
      "sayıları gösterir.")
    if synthetic:
        NOTE("A synthetic pattern is used so that every intermediate result can be compared with the true value. "
             "The same document can be built from measured data with "
             "<code>build_whitepaper.py --example private</code>.",
             "Sentetik bir desen kullanıldı; böylece her ara sonuç gerçek değerle karşılaştırılabilir. Aynı doküman "
             "ölçülmüş verilerden <code>build_whitepaper.py --example private</code> ile üretilebilir.")

    # =================================================================== 2 DIFFRACTION
    H(1, "diffraction", "Diffraction profiles and their Fourier description",
      "Kırınım profilleri ve Fourier gösterimi")
    H(2, "K", "Diffraction vector and widths in K units", "Kırınım vektörü ve K birimindeki genişlikler")
    P("A family of lattice planes with spacing d diffracts at the Bragg angle θ,",
      "Düzlemler arası uzaklığı d olan bir düzlem ailesi, Bragg açısı θ'da kırınım yapar:")
    EQ("bragg", r"\lambda=2d\sin\theta,\qquad K\equiv\frac{2\sin\theta}{\lambda}=\frac{1}{d}")
    P("K is the length of the diffraction vector g at the Bragg position. Widths are compared between "
      "reflections in K units, because the size broadening is then independent of K and the strain broadening "
      "proportional to it. Differentiating @eq:bragg with respect to θ gives the conversion of an angular width "
      "Δ(2θ) (in radians) into K units:",
      "K, Bragg konumunda kırınım vektörü g'nin uzunluğudur. Yansımalar arasında genişlikler K biriminde "
      "karşılaştırılır; çünkü bu birimde boyut genişlemesi K'den bağımsız, gerinim genişlemesi ise K ile "
      "orantılıdır. @eq:bragg'nin θ'ya göre türevi, açısal bir Δ(2θ) genişliğinin (radyan) K birimine dönüşümünü verir:")
    EQ("dK", r"\frac{\mathrm{d}K}{\mathrm{d}\theta}=\frac{2\cos\theta}{\lambda}\quad\Rightarrow\quad"
             r"\Delta K=\frac{2\cos\theta}{\lambda}\,\Delta\theta=\frac{\cos\theta\,\Delta(2\theta)}{\lambda}")
    NOTE("The factor 2 of the derivative is used up by Δθ = Δ(2θ)/2. Writing ΔK = 2cosθ·Δ(2θ)/λ doubles every "
         "width and quadruples the WH intercept. The mWH result of Shintani et al. [@shintani2010] is reproduced "
         "only with this doubled definition (@sec:validation).",
         "Türevdeki 2 çarpanı Δθ = Δ(2θ)/2 ile kullanılmış olur. ΔK = 2cosθ·Δ(2θ)/λ yazmak her genişliği iki "
         "katına, WH kesişimini dört katına çıkarır. Shintani ve ark.'nın [@shintani2010] mWH sonucu yalnızca bu "
         "iki katlı tanımla yeniden üretilebiliyor (@sec:validation).", "warn")
    H(2, "conv", "The measured profile is a convolution", "Ölçülen profil bir konvolüsyondur")
    P("Let s = K′ − K be the distance from the peak centre in K units. The physical profile f(s) of the sample is "
      "blurred by the instrument function g(s); the measured profile is their convolution,",
      "s = K′ − K, pik merkezinden K birimindeki uzaklık olsun. Numunenin fiziksel profili f(s), cihaz fonksiyonu "
      "g(s) ile bulanıklaşır; ölçülen profil ikisinin konvolüsyonudur:")
    EQ("conv", r"h(s)=\int_{-\infty}^{\infty}f(s')\,g(s-s')\,\mathrm{d}s'")
    P("The Fourier transform turns a convolution into a product. For a symmetric profile normalised to unit area "
      "only cosine terms remain, and the profile and its Fourier coefficients A(L) form the pair",
      "Fourier dönüşümü konvolüsyonu çarpıma çevirir. Birim alana normalize edilmiş simetrik bir profilde yalnızca "
      "kosinüs terimleri kalır; profil ve Fourier katsayıları A(L) şu çifti oluşturur:")
    EQ("fourier", r"I(s)=2\int_{0}^{\infty}A(L)\cos(2\pi sL)\,\mathrm{d}L,\qquad "
                  r"A(L)=\int_{-\infty}^{\infty}I(s)\cos(2\pi sL)\,\mathrm{d}s,\qquad A(0)=1")
    P("Warren and Averbach [@warren1950] showed that the physical Fourier coefficient is itself a product of a size "
      "part and a distortion part. With the instrument the measured coefficient is",
      "Warren ve Averbach [@warren1950], fiziksel Fourier katsayısının da bir boyut ve bir bozulma kısmının çarpımı "
      "olduğunu gösterdi. Cihazla birlikte ölçülen katsayı:")
    EQ("product", r"A(L)=A^S(L)\;A^D(L)\;A^I(L)")
    P("@eq:product is the backbone of everything that follows. The mWA (@sec:mwa) separates $A^S$ and $A^D$ "
      "through their different dependence on the reflection, and the whole-profile fit (@sec:wp) builds A(L) from "
      "physical models of the three factors and transforms it back with @eq:fourier.",
      "@eq:product, bundan sonraki her şeyin omurgasıdır. mWA (@sec:mwa), $A^S$ ve $A^D$'yi yansımaya farklı "
      "bağlılıklarından ayırır; tam profil uydurması (@sec:wp) ise A(L)'yi üç çarpanın fiziksel modellerinden kurar "
      "ve @eq:fourier ile profile geri dönüştürür.")
    H(2, "L", "Physical meaning of the Fourier length L", "Fourier uzunluğu L'nin fiziksel anlamı")
    P("Divide the crystal into columns of unit cells parallel to the diffraction vector. A(L) is an average over all "
      "pairs of cells that lie a distance L apart in the same column. $A^S(L)$ is the fraction of such pairs whose "
      "two cells are in the same crystallite (otherwise they do not scatter coherently), and $A^D(L)$ is the average "
      "phase factor $\\langle\\cos 2\\pi\\,\\mathbf{g}\\cdot[\\mathbf{u}(\\mathbf{r}+L)-\\mathbf{u}(\\mathbf{r})]\\rangle$, where u is the "
      "displacement of the cells from their ideal positions [@warren1969]. Small L probes short-range distortion, "
      "large L the size of the coherent domains. This is why the strain information sits in the small-L part of "
      "A(L), that is, in the tails of the peak.",
      "Kristali kırınım vektörüne paralel birim hücre sütunlarına bölelim. A(L), aynı sütunda birbirinden L "
      "uzaklıktaki tüm hücre çiftleri üzerinden bir ortalamadır. $A^S(L)$, iki hücresi aynı kristalitte olan "
      "çiftlerin oranıdır (aksi hâlde eş evreli saçılmazlar); $A^D(L)$ ise ortalama faz çarpanı "
      "$\\langle\\cos 2\\pi\\,\\mathbf{g}\\cdot[\\mathbf{u}(\\mathbf{r}+L)-\\mathbf{u}(\\mathbf{r})]\\rangle$'dir; burada u "
      "hücrelerin ideal konumlarından yer değiştirmesidir [@warren1969]. Küçük L kısa erimli bozulmayı, büyük L "
      "koherent bölgelerin boyutunu yoklar. Gerinim bilgisinin A(L)'nin küçük-L kısmında, yani pikin kuyruklarında "
      "durmasının nedeni budur.")

    # =================================================================== 3 PEAKS
    H(1, "peaks", "Peak fitting", "Pik uydurma")
    H(2, "voigt", "The Voigt function", "Voigt fonksiyonu")
    P("Every reflection is described by a Voigt function, the convolution of a Gaussian and a Lorentzian. In the "
      "program the two are characterised by their component FWHMs $w_G$ and $w_L$ (not by the total width) "
      "[@balzar1993; @hajyakbary2015]:",
      "Her yansıma bir Voigt fonksiyonuyla, yani bir Gauss ile bir Lorentz'in konvolüsyonuyla tanımlanır. Programda "
      "ikisi toplam genişlikle değil, bileşen FWHM'leri $w_G$ ve $w_L$ ile tanımlanır [@balzar1993; @hajyakbary2015]:")
    EQ("voigt", r"V(s;w_G,w_L)=\int_{-\infty}^{\infty}\frac{2\sqrt{\ln2}}{\sqrt{\pi}\,w_G}\,"
                r"e^{-4\ln2\,s'^2/w_G^2}\;\frac{w_L/2\pi}{(s-s')^2+(w_L/2)^2}\,\mathrm{d}s'")
    P("The total FWHM of the Voigt function is computed with the approximation of Olivero and Longbothum "
      "[@olivero1977], accurate to about 0.02 %:",
      "Voigt fonksiyonunun toplam FWHM'si, yaklaşık %0,02 doğruluklu Olivero ve Longbothum [@olivero1977] "
      "yaklaşımıyla hesaplanır:")
    EQ("olivero", r"\Delta K\simeq0.5346\,w_L+\sqrt{0.2166\,w_L^2+w_G^2}")
    H(2, "doublet", "Kα1/Kα2 doublets, overlaps and weights", "Kα1/Kα2 ikilileri, çakışmalar ve ağırlıklar")
    P("Cu Kα radiation contains two lines, Kα1 (λ₁) and Kα2 (λ₂), with an intensity ratio close to 1/2. Both lines "
      "are diffracted by the same planes, so in K space they produce the same physical profile; in 2θ the Kα2 "
      "component appears at the angle that satisfies @eq:bragg with λ₂:",
      "Cu Kα ışınımı, şiddet oranı yaklaşık 1/2 olan iki çizgi içerir: Kα1 (λ₁) ve Kα2 (λ₂). İki çizgi de aynı "
      "düzlemlerden kırınıma uğradığı için K uzayında aynı fiziksel profili verir; 2θ'da Kα2 bileşeni, @eq:bragg'yi "
      "λ₂ ile sağlayan açıda görünür:")
    EQ("ka2", r"2\theta_2=2\arcsin\left(\frac{\lambda_2}{\lambda_1}\sin\theta_1\right)")
    P("A fitting window contains one reflection or a group of overlapping reflections (00.2 + 10.1 with the β 110 "
      "position, 11.2 + 20.1) and a linear background. The model of a window with reflections j is",
      "Bir uydurma penceresi tek bir yansıma ya da çakışan bir yansıma grubu (β 110 konumuyla birlikte 00.2 + 10.1; "
      "11.2 + 20.1) ve doğrusal bir zemin içerir. j yansımalarından oluşan bir pencerenin modeli:")
    EQ("peakmodel", r"y(2\theta)=b_0+b_1\,(2\theta-\overline{2\theta})+\sum_j A_j\left[V(2\theta-2\theta_j)+"
                    r"r\,V(2\theta-2\theta_{2,j})\right],\qquad r=I_{K\alpha_2}/I_{K\alpha_1}")
    P("with r = 0.5 for raw data and r = 0 when the pattern was exported after Kα2 stripping (read from the UXD or RAW file "
      "header, or set by the user). The parameters are found by minimising the Poisson-weighted sum of squares, "
      "because the variance of a count y is y:",
      "Ham veride r = 0,5, desen Kα2 ayıklandıktan sonra dışa aktarılmışsa r = 0'dır (UXD ya da RAW dosya başlığından "
      "okunur ya da kullanıcı belirler). Parametreler Poisson ağırlıklı kareler toplamı en küçüklenerek bulunur, çünkü bir y "
      "sayımının varyansı y'dir:")
    EQ("chi2", r"\chi^2=\sum_i\frac{\left(y_i-\hat{y}_i\right)^2}{\max(y_i,1)}")
    H(2, "strip", "Why raw data are preferred to Kα2-stripped data", "Ham veri neden Kα2 ayıklanmış veriye tercih edilir")
    P("The usual Kα2 stripping (Rachinger correction [@rachinger1948]) removes, point by point, half of the "
      "intensity measured at the angle where the Kα2 contribution originates. It assumes that the Kα2 profile is an "
      "exact, shifted copy of the Kα1 profile with ratio exactly 1/2. Any deviation (spectral line shapes, ratio, "
      "the angle dependence of the shift) leaves residual dips, shoulders or negative counts, and the recursion "
      "propagates the counting noise into the corrected profile. These errors sit in the peak tails, exactly where "
      "the dislocation information is (@sec:L). AutoDisloc therefore models the doublet explicitly "
      "(@eq:peakmodel) and recommends unstripped, unsmoothed data for both the samples and the line standard.",
      "Yaygın Kα2 ayıklama (Rachinger düzeltmesi [@rachinger1948]), Kα2 katkısının kaynaklandığı açıda ölçülen "
      "şiddetin yarısını nokta nokta çıkarır. Kα2 profilinin Kα1 profilinin oranı tam 1/2 olan, kaydırılmış birebir "
      "kopyası olduğunu varsayar. Her sapma (spektral çizgi şekilleri, oran, kaymanın açıya bağlılığı) artık "
      "çukurlar, omuzlar ya da negatif sayımlar bırakır; özyineleme de sayım gürültüsünü düzeltilmiş profile taşır. "
      "Bu hatalar tam da dislokasyon bilgisinin bulunduğu yerde, pik kuyruklarındadır (@sec:L). Bu yüzden AutoDisloc "
      "ikiliyi açıkça modeller (@eq:peakmodel) ve hem numuneler hem çizgi standardı için ayıklanmamış, yumuşatılmamış "
      "veri önerir.")
    H(2, "lattice", "Lattice parameters", "Kafes parametreleri")
    P("In Bragg–Brentano geometry the dominant systematic error of peak positions is the specimen displacement s "
      "(the specimen surface lies a distance s off the focusing circle of radius R), which shifts every reflection by "
      "$\\Delta(2\\theta)=-2s\\cos\\theta/R$ and therefore changes $\\sin^2\\theta$ by "
      "$-(2s/R)\\sin\\theta\\cos^2\\theta$. The hexagonal lattice parameters follow from the fitted Kα1 positions by "
      "Cohen's linear least squares [@cohen1935] with this drift term:",
      "Bragg–Brentano geometrisinde pik konumlarının baskın sistematik hatası numune yüksekliği hatası s'dir (numune "
      "yüzeyi R yarıçaplı odaklama çemberinden s kadar uzaktadır). Bu hata her yansımayı "
      "$\\Delta(2\\theta)=-2s\\cos\\theta/R$ kadar kaydırır, dolayısıyla $\\sin^2\\theta$'yı "
      "$-(2s/R)\\sin\\theta\\cos^2\\theta$ kadar değiştirir. Hekzagonal kafes parametreleri, uydurulan Kα1 "
      "konumlarından bu sürüklenme terimini içeren Cohen doğrusal en küçük kareler yöntemiyle [@cohen1935] bulunur:")
    EQ("lattice", r"\sin^2\theta=\frac{\lambda^2}{3a^2}\,(h^2+hk+k^2)+\frac{\lambda^2}{4c^2}\,l^2"
                  r"-\frac{2s}{R}\,\sin\theta\cos^2\theta")
    P("The three coefficients are linear unknowns; their standard errors follow from the residual variance and "
      "give the errors of a, c and c/a. The cubic β lattice parameter is computed from every significant β "
      "reflection after correcting its position for the same s, $a_\\beta=\\lambda\\sqrt{h^2+k^2+l^2}/(2\\sin\\theta)$. "
      "The lattice parameters enter the contrast variable x (@eq:hex) and are reported for every sample "
      "(figure, table and Excel report). Optionally the goniometer zero shift z of the line standard (@eq:zero) is "
      "subtracted from the positions first. The fit windows are placed with nominal lattice parameters of the "
      "alloy; when these would misplace a reflection by more than 0.35° (another alloy, another wavelength, a "
      "large goniometer offset) they are replaced by values matched to the strongest maxima of the pattern.",
      "Üç katsayı doğrusal bilinmeyendir; standart hataları artık varyansından çıkar ve a, c ile c/a'nın hatalarını "
      "verir. Kübik β kafes parametresi, her anlamlı β yansımasının konumu aynı s ile düzeltildikten sonra "
      "$a_\\beta=\\lambda\\sqrt{h^2+k^2+l^2}/(2\\sin\\theta)$ ile hesaplanır. Kafes parametreleri kontrast "
      "değişkeni x'e (@eq:hex) girer ve her numune için raporlanır (şekil, tablo ve Excel raporu). İsteğe bağlı "
      "olarak çizgi standardının gonyometre sıfır kayması z (@eq:zero) önce konumlardan çıkarılır. Uydurma "
      "pencereleri alaşımın nominal kafes parametreleriyle yerleştirilir; bunlar bir yansımayı 0,35°'den fazla "
      "kaydıracaksa (başka alaşım, başka dalga boyu, büyük gonyometre kayması) desenin en güçlü tepelerine "
      "eşleştirilmiş değerlerle değiştirilir.")
    FIG("pattern", "pattern", "Pattern of the worked example (log scale) with the indexed α reflections and the "
        "Wilkens whole-profile model of @sec:wp. Lower panel: measured − model.",
        "Uygulamalı örneğin deseni (log ölçek), indekslenmiş α yansımaları ve @sec:wp'deki Wilkens tam profil modeli. "
        "Alt panel: ölçülen − model.")
    FIG("doublet", "peak", "Voigt doublet fit of the 00.2 + 10.1 window: Kα1 (blue) and Kα2 (orange) components of "
        "@eq:peakmodel.",
        "00.2 + 10.1 penceresinin Voigt ikilisi uydurması: @eq:peakmodel'in Kα1 (mavi) ve Kα2 (turuncu) bileşenleri.")
    EX("The fitted lattice parameters are a = «a_A» Å and c = «c_A» Å (specimen displacement «disp» µm). @tab:peaks lists the widths of the eight α "
       "reflections that enter the analysis.",
       "Uydurulan kafes parametreleri a = «a_A» Å ve c = «c_A» Å (numune yüksekliği hatası «disp» µm). @tab:peaks, analize giren sekiz α yansımasının "
       "genişliklerini listeler.")
    rows = []
    for _, r in ex.peaks.iterrows():
        rows.append([r["hkl"], f"{r['2theta']:.3f}", f"{r['K']:.3f}", f"{r['wG_m'] * 1e3:.2f}", f"{r['wL_m'] * 1e3:.2f}",
                     f"{r['wG_t'] * 1e3:.2f}", f"{r['wL_t'] * 1e3:.2f}", f"{r['x']:.3f}", f"{r['b2C_hkl']:.4f}"])
    TAB("peaks", "Reflections of the worked example. Widths in 10<sup>−3</sup> nm<sup>−1</sup>; m: measured, "
        "t: instrument-corrected (@eq:gcorr). b²C̄<sub>hkl</sub> from the constrained mWH (@sec:mwh).",
        "Uygulamalı örneğin yansımaları. Genişlikler 10<sup>−3</sup> nm<sup>−1</sup> biriminde; m: ölçülen, "
        "t: cihazdan arındırılmış (@eq:gcorr). b²C̄<sub>hkl</sub> kısıtlı mWH'den (@sec:mwh).",
        ["hkl", "2θ (°)", "K (nm⁻¹)", "w<sub>G,m</sub>", "w<sub>L,m</sub>", "w<sub>G,t</sub>", "w<sub>L,t</sub>",
         "x", "b²C̄<sub>hkl</sub> (nm²)"], rows)

    # =================================================================== 4 INSTRUMENT
    H(1, "instrument", "Instrumental broadening", "Cihaz genişlemesi")
    H(2, "standard", "Instrument model from a line standard", "Çizgi standardından cihaz modeli")
    P("A line standard is measured with the same optics and fitted with the same Voigt model. Its component widths "
      "in K units are described by low-order polynomials,",
      "Bir çizgi standardı aynı optikle ölçülür ve aynı Voigt modeliyle uydurulur. K birimindeki bileşen genişlikleri "
      "düşük dereceli polinomlarla tanımlanır:")
    EQ("instpoly", r"w_{G,s}(K)=\sum_k g_kK^k,\qquad w_{L,s}(K)=\sum_k l_kK^k")
    P("fitted robustly (points more than three median absolute deviations from a first fit are dropped). "
      "Outside the K range of the standard the model is extrapolated and a warning is issued.",
      "Bu polinomlar dayanıklı biçimde uydurulur (ilk uydurmadan üç medyan mutlak sapmadan uzak noktalar atılır). "
      "Standardın K aralığının dışında model ekstrapole edilir ve uyarı verilir.")
    H(2, "stdindex", "Indexing, zero shift and wavelength check", "İndeksleme, sıfır kayması ve dalga boyu denetimi")
    P("The lattice parameters of the standard (defaults: LaB<sub>6</sub> a = 4.156826 Å [@black2020], Si "
      "a = 5.431144 Å [@nist640f], CeO<sub>2</sub> and corundum nominal; all editable) give the reflection positions "
      "through Bragg's law (@eq:bragg) and the reflection conditions of the space group: none for Pm-3m (LaB<sub>6</sub>); "
      "h, k, l unmixed for Fm-3m (CeO<sub>2</sub>), and in addition h + k + l = 4n when all are even for Fd-3m (Si); "
      "−h + k + l = 3n, and l even for h h̄ 0 l type reflections, for R-3c in hexagonal axes (corundum). A scan "
      "of a constant offset (±0.5°) finds the assignment that indexes most of the fitted peaks; peaks further than "
      "0.1° from every reflection are not used for @eq:instpoly. The remaining deviations follow",
      "Standardın kafes parametreleri (varsayılanlar: LaB<sub>6</sub> a = 4,156826 Å [@black2020], Si "
      "a = 5,431144 Å [@nist640f], CeO<sub>2</sub> ve korundum nominal; hepsi değiştirilebilir), Bragg yasası "
      "(@eq:bragg) ve uzay grubunun yansıma koşullarıyla yansıma konumlarını verir: Pm-3m (LaB<sub>6</sub>) için koşul "
      "yoktur; Fm-3m (CeO<sub>2</sub>) için h, k, l karışık olmamalıdır, Fd-3m (Si) için ayrıca hepsi çiftse "
      "h + k + l = 4n olmalıdır; hekzagonal eksenlerde R-3c (korundum) için −h + k + l = 3n ve h h̄ 0 l tipi "
      "yansımalarda l çift olmalıdır. Sabit bir kaymanın (±0,5°) taranması, uydurulan piklerin en çoğunu "
      "indeksleyen eşleşmeyi bulur; her yansımadan 0,1°'den uzak pikler @eq:instpoly için kullanılmaz. Kalan "
      "sapmalar şu bağıntıya uyar:")
    EQ("zero", r"2\theta_{\mathrm{obs}}-2\theta_{\mathrm{calc}}=z-\frac{360^\circ}{\pi}\,\frac{s}{R}\,\cos\theta")
    P("which is linear in the zero shift z of the goniometer and the specimen displacement s of the standard and is "
      "solved by least squares. z belongs to the instrument and can be subtracted from the sample positions before "
      "@eq:lattice; s belongs to each specimen and is fitted for every sample by @eq:lattice itself. Because 1 and "
      "cos θ are strongly correlated over the usual angular range, and an error in the lattice parameter of the "
      "standard adds a term proportional to tan θ, z is reliable only for a standard with a certified lattice "
      "parameter; its use is therefore optional. When fewer than 60 % of the peaks can be indexed, the standard, "
      "its lattice parameter or the wavelength is wrong and a warning is issued.",
      "Bu bağıntı gonyometrenin sıfır kayması z'ye ve standardın yüzey yer değiştirmesi s'ye göre doğrusaldır ve en "
      "küçük karelerle çözülür. z cihaza aittir ve @eq:lattice'ten önce numune konumlarından çıkarılabilir; s her "
      "numuneye özgüdür ve her numunede @eq:lattice ile ayrıca uydurulur. Olağan açı aralığında 1 ile cos θ güçlü "
      "biçimde ilişkili olduğundan ve standardın kafes parametresindeki bir hata tan θ ile orantılı bir terim "
      "eklediğinden, z yalnızca kafes parametresi sertifikalı bir standartla güvenilirdir; bu yüzden kullanımı "
      "isteğe bağlıdır. Piklerin %60'ından azı indekslenebiliyorsa standart, kafes parametresi ya da dalga boyu "
      "yanlıştır ve uyarı verilir.")
    P("The wavelengths λ<sub>1</sub>, λ<sub>2</sub>, the Kα2/Kα1 ratio and the goniometer radius are read from the "
      "data files (Bruker RAW and UXD, PANalytical XRDML, header lines of two-column files). Values a file does not "
      "contain are taken as Cu Kα (λ<sub>1</sub> = 1.540598 Å, λ<sub>2</sub> = 1.544426 Å [@prince2004]), 0.5 and "
      "250 mm, flagged as assumed and reported; tabulated Kα wavelengths of Co, Fe, Cr, Mo and Ag [@prince2004] or "
      "custom values can be chosen instead. A sample wavelength that differs from that of the standard is reported, "
      "because the instrument function in K units belongs to one tube and one set of optics.",
      "Dalga boyları λ<sub>1</sub>, λ<sub>2</sub>, Kα2/Kα1 oranı ve gonyometre yarıçapı veri dosyalarından okunur "
      "(Bruker RAW ve UXD, PANalytical XRDML, iki sütunlu dosyaların başlık satırları). Dosyada bulunmayan değerler Cu "
      "Kα (λ<sub>1</sub> = 1,540598 Å, λ<sub>2</sub> = 1,544426 Å [@prince2004]), 0,5 ve 250 mm alınır, varsayılan "
      "olarak işaretlenir ve raporlanır; bunların yerine Co, Fe, Cr, Mo ve Ag'nin tablo Kα dalga boyları "
      "[@prince2004] ya da özel değerler seçilebilir. Numunenin dalga boyu standardınkinden farklıysa bu bildirilir, "
      "çünkü K birimindeki cihaz fonksiyonu tek bir tüpe ve tek bir optik düzene aittir.")
    EX("Corundum standard of this work (nominal corundum lattice): «std_n» peaks indexed, rms residual «std_rms»°, "
       "z = «std_z»°, s = «std_s» µm.",
       "Bu çalışmanın korundum standardı (nominal korundum kafesi): «std_n» pik indekslendi, rms artık «std_rms»°, "
       "z = «std_z»°, s = «std_s» µm.")
    H(2, "widthcorr", "Correction of widths", "Genişliklerin düzeltilmesi")
    P("Because the Fourier transform of a convolution is a product (@eq:product), and the Fourier coefficients of a "
      "Gaussian and of a Lorentzian are $\\exp(-\\pi^2w_G^2L^2/4\\ln2)$ and $\\exp(-\\pi w_LL)$ (@sec:voigtft), "
      "convolving two Voigt functions adds the squares of the Gaussian widths and the Lorentzian widths themselves. "
      "The physical component widths are therefore",
      "Konvolüsyonun Fourier dönüşümü bir çarpım olduğundan (@eq:product) ve bir Gauss ile bir Lorentz'in Fourier "
      "katsayıları $\\exp(-\\pi^2w_G^2L^2/4\\ln2)$ ve $\\exp(-\\pi w_LL)$ olduğundan (@sec:voigtft), iki Voigt "
      "fonksiyonunun konvolüsyonunda Gauss genişliklerinin kareleri, Lorentz genişliklerinin ise kendileri toplanır. "
      "Fiziksel bileşen genişlikleri bu yüzden:")
    EQ("gcorr", r"w_{G,t}^2=w_{G,m}^2-w_{G,s}^2,\qquad w_{L,t}=w_{L,m}-w_{L,s}")
    P("(subscripts m: measured, s: standard, t: true). This exact relation is used in the mWH and the Voigt-mWA; a "
      "negative result is set to zero and reported. In the whole-profile fit the instrument enters instead as the "
      "multiplicative factor",
      "(alt indisler m: ölçülen, s: standart, t: gerçek). Bu kesin bağıntı mWH'de ve Voigt-mWA'da kullanılır; negatif "
      "sonuç sıfırlanır ve raporlanır. Tam profil uydurmasında ise cihaz şu çarpımsal faktör olarak modele girer:")
    EQ("AI", r"A^I(L;K)=\exp\left(-\pi\,w_{L,s}(K)\,L-\frac{\pi^2}{4\ln2}\,w_{G,s}(K)^2L^2\right)")
    P("which is the Stokes correction [@stokes1948] written with the model of the standard: no subtraction and no "
      "negative widths occur.",
      "Bu, standardın modeliyle yazılmış Stokes düzeltmesidir [@stokes1948]: çıkarma yapılmaz ve negatif genişlik "
      "oluşmaz.")
    FIG("inst", "inst", "Component widths of the line standard (corundum) and the linear instrument model of "
        "@eq:instpoly. The standard is almost purely Gaussian.",
        "Çizgi standardının (korundum) bileşen genişlikleri ve @eq:instpoly'nin doğrusal cihaz modeli. Standart "
        "neredeyse saf Gauss profillidir.", 0.62)
    EX("Example instrument model (nm<sup>−1</sup>, highest power first): g = [«inst_g»], l = [«inst_l»], valid for "
       "K = «kmin»–«kmax» nm<sup>−1</sup>.",
       "Örnek cihaz modeli (nm<sup>−1</sup>, en yüksek kuvvet önce): g = [«inst_g»], l = [«inst_l»]; geçerlilik "
       "aralığı K = «kmin»–«kmax» nm<sup>−1</sup>.")

    # =================================================================== 5 THEORY
    H(1, "theory", "Strain broadening by dislocations", "Dislokasyonların neden olduğu gerinim genişlemesi")
    H(2, "AD", "The distortion Fourier coefficient", "Bozulma Fourier katsayısı")
    P("For two cells a distance L apart along g, the phase difference of the scattered waves is "
      "$\\varphi=2\\pi\\,\\mathbf{g}\\cdot\\Delta\\mathbf{u}=2\\pi gL\\,\\varepsilon_{g,L}$, where "
      "$\\varepsilon_{g,L}$ is the mean strain along g over the distance L. The distortion coefficient is the "
      "average of the phase factor. If the strains are Gaussian distributed with zero mean, "
      "$\\langle e^{i\\varphi}\\rangle=e^{-\\langle\\varphi^2\\rangle/2}$ and",
      "g yönünde birbirinden L uzaklıktaki iki hücreden saçılan dalgaların faz farkı "
      "$\\varphi=2\\pi\\,\\mathbf{g}\\cdot\\Delta\\mathbf{u}=2\\pi gL\\,\\varepsilon_{g,L}$'dir; burada "
      "$\\varepsilon_{g,L}$, L uzaklığı boyunca g yönündeki ortalama gerinimdir. Bozulma katsayısı faz çarpanının "
      "ortalamasıdır. Gerinimler sıfır ortalamalı Gauss dağılımına uyuyorsa "
      "$\\langle e^{i\\varphi}\\rangle=e^{-\\langle\\varphi^2\\rangle/2}$ olur ve")
    EQ("ADgauss", r"A^D(L)=\left\langle\exp\left(2\pi i\,\mathbf{g}\cdot[\mathbf{u}(\mathbf{r}+L)-"
                  r"\mathbf{u}(\mathbf{r})]\right)\right\rangle=\exp\left(-2\pi^2g^2L^2\langle\varepsilon^2_{g,L}\rangle\right)")
    P("[@warren1969]. The whole problem of the strain broadening is thus to know how the mean-square strain depends "
      "on L.",
      "elde edilir [@warren1969]. Gerinim genişlemesinin bütün sorunu, ortalama kare gerinimin L'ye nasıl bağlı "
      "olduğunu bilmektir.")
    H(2, "wilkens", "The Krivoglaz–Wilkens mean-square strain", "Krivoglaz–Wilkens ortalama kare gerinimi")
    P("Krivoglaz [@krivoglaz1996] and Wilkens [@wilkens1970; @wilkens1970b] computed $\\langle\\varepsilon^2_{g,L}\\rangle$ "
      "for straight dislocations distributed at random inside regions of size $R_e^*$ (the restrictedly random "
      "distribution). The strain field of each dislocation decays as 1/r, and $R_e^*$ is the distance beyond which "
      "the fields of neighbouring dislocations cancel. The result is",
      "Krivoglaz [@krivoglaz1996] ve Wilkens [@wilkens1970; @wilkens1970b], $R_e^*$ boyutundaki bölgeler içinde "
      "rastgele dağılmış düz dislokasyonlar (sınırlı rastgele dağılım) için $\\langle\\varepsilon^2_{g,L}\\rangle$'yi "
      "hesapladı. Her dislokasyonun gerinim alanı 1/r ile azalır; $R_e^*$ komşu dislokasyonların alanlarının "
      "birbirini sönümlediği uzaklıktır. Sonuç:")
    EQ("eps2", r"\langle\varepsilon^2_{g,L}\rangle=\frac{\rho\,C\,b^2}{4\pi}\,f(\eta),\qquad \eta=\frac{L}{R_e^*}")
    P("Inserting @eq:eps2 into @eq:ADgauss with g = K gives the dislocation Fourier coefficient used throughout the "
      "program:",
      "@eq:eps2'yi g = K ile @eq:ADgauss'ta yerine koymak, program boyunca kullanılan dislokasyon Fourier katsayısını "
      "verir:")
    EQ("AD", r"A^D(L)=\exp\left(-2\pi^2K^2L^2\,\frac{\rho Cb^2}{4\pi}f(\eta)\right)="
             r"\exp\left(-\frac{\pi}{2}\,\rho\,b^2C\,K^2L^2f(\eta)\right)")
    P("Three facts of @eq:AD drive the rest of the analysis. The broadening grows with $K^2$, so it separates from "
      "the K-independent size broadening. It is proportional to $b^2C$, so reflections with different contrast "
      "broaden differently (@sec:contrast). And it depends on ρ and on the arrangement through f(η).",
      "@eq:AD'nin üç özelliği analizin geri kalanını belirler. Genişleme $K^2$ ile artar; böylece K'den bağımsız "
      "boyut genişlemesinden ayrılır. $b^2C$ ile orantılıdır; böylece kontrastı farklı yansımalar farklı genişler "
      "(@sec:contrast). Ve ρ'ya ve f(η) üzerinden dislokasyon düzenine bağlıdır.")
    H(2, "ffunc", "The Wilkens function and the arrangement parameter", "Wilkens fonksiyonu ve düzen parametresi")
    P("Wilkens' closed form of f [@wilkens1970b] is, for η ≤ 1,",
      "Wilkens'in f için kapalı biçimi [@wilkens1970b], η ≤ 1 için:")
    EQ("f1", r"f(\eta)=-\ln\eta+\frac{7}{4}-\ln2+\frac{512}{90\pi\eta}+\frac{2}{\pi}\left(1-\frac{1}{4\eta^2}\right)"
             r"\int_0^{\eta}\frac{\arcsin V}{V}\,\mathrm{d}V")
    EQ("f2", r"\quad-\frac{1}{\pi}\left(\frac{769}{180\eta}+\frac{41\eta}{90}+\frac{2\eta^3}{90}\right)\sqrt{1-\eta^2}"
             r"-\frac{1}{\pi}\left(\frac{11}{12\eta^2}+\frac{7}{2}+\frac{\eta^2}{3}\right)\arcsin\eta+\frac{\eta^2}{6}")
    P("and for η > 1",
      "ve η > 1 için:")
    EQ("f3", r"f(\eta)=\frac{512}{90\pi\eta}-\left(\frac{11}{24}+\frac{1}{4}\ln2\eta\right)\frac{1}{\eta^2}")
    P("For small η only the logarithm survives, $f\\to-\\ln\\eta+7/4-\\ln2$. AutoDisloc writes the argument as "
      "η = L/R_e* (@eq:eps2), so that $f\\to\\ln(R_e/L)$ with",
      "Küçük η için yalnızca logaritma kalır: $f\\to-\\ln\\eta+7/4-\\ln2$. AutoDisloc argümanı η = L/R_e* olarak "
      "yazar (@eq:eps2); böylece $f\\to\\ln(R_e/L)$ olur, burada")
    EQ("Re", r"R_e=\frac{e^{7/4}}{2}\,R_e^*=2.877\,R_e^*,\qquad M^*=R_e^*\sqrt{\rho}")
    P("$R_e$ is the cut-off radius of the logarithmic (mWA) form of @eq:AD [@ungar2001] (Eq. 3); $R_e^*$ and $M^*$ "
      "are the quantities the program reports. <b>Convention.</b> Wilkens' closed form @eq:f1–@eq:f3 is published "
      "with the argument $\\eta=\\tfrac{1}{2}e^{-1/4}L/R_e^*$ [@ribarik2001] (Eq. 4 there, which reproduces Eqs. A6–A8 of [@wilkens1970b]), and "
      "MWP-fit/CMWP report $M^*=R_e^*\\sqrt{\\rho}$ with this $R_e^*$, for which $R_e=e^2R_e^*$ [@ribarik2001]. "
      "The $R_e^*$ of the program contains the factor $\\tfrac{1}{2}e^{-1/4}$; for the same physical state",
      "$R_e$, @eq:AD'nin logaritmik (mWA) biçimindeki kesme yarıçapıdır [@ungar2001] (Denk. 3); $R_e^*$ ve $M^*$ "
      "programın raporladığı büyüklüklerdir. <b>Tanım farkı.</b> Wilkens'in kapalı biçimi @eq:f1–@eq:f3, "
      "$\\eta=\\tfrac{1}{2}e^{-1/4}L/R_e^*$ argümanıyla yayımlanmıştır [@ribarik2001] (oradaki Denk. 4, [@wilkens1970b]'nin Denk. A6–A8'ini verir), "
      "MWP-fit/CMWP de bu $R_e^*$ ile $M^*=R_e^*\\sqrt{\\rho}$ raporlar; bu tanımda $R_e=e^2R_e^*$'dır "
      "[@ribarik2001]. Programın $R_e^*$'ı $\\tfrac{1}{2}e^{-1/4}$ çarpanını içerir; aynı fiziksel durum için")
    EQ("Mconv", r"R^*_{e,\mathrm{CMWP}}=\frac{R_e^*}{2e^{1/4}}=\frac{R_e^*}{2.568},\qquad "
                r"M^*_{\mathrm{CMWP}}=\frac{M^*}{2e^{1/4}}=\frac{M^*}{2.568}")
    P("Divide the M* and R_e* of AutoDisloc by 2.568 before comparing them with values from MWP-fit/CMWP. The "
      "arrangement parameter $M=R_e\\sqrt{\\rho}$ of [@ungar2001] (Eq. 25a, with the $R_e$ of the logarithmic form) "
      "equals 2.877 M*. ρ is the same in every convention, because the model is the same and only the name of the "
      "fitted length changes. The dimensionless arrangement parameter [@wilkens1970] describes the arrangement: "
      "small values mean that the strain fields are screened within a short distance (dipoles, walls), large values "
      "weakly correlated dislocations. In the program f is tabulated once on 1500 logarithmically spaced η values "
      "(the integral by adaptive quadrature) and interpolated; below η = 10⁻⁴ the exact logarithmic limit is used.",
      "AutoDisloc'un M* ve R_e* değerlerini MWP-fit/CMWP değerleriyle karşılaştırmadan önce 2,568'e bölün. "
      "[@ungar2001]'in düzen parametresi $M=R_e\\sqrt{\\rho}$ (Denk. 25a, logaritmik biçimdeki $R_e$ ile) 2,877 M*'a "
      "eşittir. ρ her tanımda aynıdır; çünkü model aynıdır, yalnızca uydurulan uzunluğun adı değişir. Boyutsuz "
      "düzen parametresi [@wilkens1970] düzeni tanımlar: küçük değerler gerinim alanlarının kısa bir uzaklıkta "
      "perdelendiği (dipoller, duvarlar), büyük değerler ise zayıf ilişkili dislokasyonlar anlamına gelir. "
      "Programda f, logaritmik aralıklı 1500 η değerinde bir kez tablolanır (integral uyarlamalı kuadratürle) ve "
      "aradeğerlenir; η = 10⁻⁴'ün altında kesin logaritmik limit kullanılır.")
    FIG("wilkens", "wilkens", "Wilkens function f(η) of @eq:f1–@eq:f3 and the logarithmic approximation used by the "
        "mWA. The approximation holds only for L ≪ R<sub>e</sub>.",
        "@eq:f1–@eq:f3'teki Wilkens fonksiyonu f(η) ve mWA'nın kullandığı logaritmik yaklaşım. Yaklaşım yalnızca "
        "L ≪ R<sub>e</sub> için geçerlidir.", 0.62)

    # =================================================================== 6 CONTRAST
    H(1, "contrast", "Dislocation contrast factors of hexagonal crystals", "Hekzagonal kristallerde dislokasyon kontrast faktörleri")
    H(2, "corigin", "Origin of the contrast factor", "Kontrast faktörünün kaynağı")
    P("The strain $\\varepsilon_{g,L}$ in @eq:ADgauss is the component of the displacement gradient along g. For a "
      "given dislocation it depends on the angles between g, the Burgers vector b and the line direction, and on "
      "the elastic constants. The contrast factor C collects this dependence; a dislocation with $\\mathbf{g}\\cdot\\mathbf{b}=0$ "
      "(and, for edge dislocations, $\\mathbf{g}\\cdot(\\mathbf{b}\\times\\mathbf{l})=0$) is nearly invisible. In an "
      "untextured polycrystal containing all equivalent slip systems with equal probability, C is averaged over "
      "them; the average depends only on the reflection hkl [@ungar1999].",
      "@eq:ADgauss'taki $\\varepsilon_{g,L}$ gerinimi, yer değiştirme gradyanının g yönündeki bileşenidir. Belirli bir "
      "dislokasyon için g, Burgers vektörü b ve çizgi yönü arasındaki açılara ve elastik sabitlere bağlıdır. Kontrast "
      "faktörü C bu bağlılığı toplar; $\\mathbf{g}\\cdot\\mathbf{b}=0$ olan (kenar dislokasyonlarında ayrıca "
      "$\\mathbf{g}\\cdot(\\mathbf{b}\\times\\mathbf{l})=0$ olan) bir dislokasyon neredeyse görünmezdir. Tüm eşdeğer "
      "kayma sistemlerini eşit olasılıkla içeren dokusuz bir çok kristalde C bunlar üzerinden ortalanır; ortalama "
      "yalnızca hkl yansımasına bağlıdır [@ungar1999].")
    H(2, "hexform", "The hexagonal form", "Hekzagonal biçim")
    P("For hexagonal crystals the average is a fourth-order invariant of the direction cosines of g, which reduces "
      "to a quadratic in one variable [@dragomir2002]:",
      "Hekzagonal kristallerde ortalama, g'nin doğrultu kosinüslerinin dördüncü dereceden bir değişmezidir ve tek bir "
      "değişkende ikinci dereceden bir ifadeye indirgenir [@dragomir2002]:")
    EQ("hex", r"\overline{C}_{hk.l}=\overline{C}_{hk.0}\left(1+q_1x+q_2x^2\right),\qquad x=\frac{2}{3}\left(\frac{l}{Ka}\right)^2")
    P("$\\overline{C}_{hk.0}$ is the value of the hk.0 reflections, and $q_1$, $q_2$ depend on the slip system, the "
      "dislocation character and the elastic constants. x is zero for hk.0 reflections and grows with the l index.",
      "$\\overline{C}_{hk.0}$, hk.0 yansımalarının değeridir; $q_1$ ve $q_2$ kayma sistemine, dislokasyon karakterine "
      "ve elastik sabitlere bağlıdır. x, hk.0 yansımaları için sıfırdır ve l indisiyle büyür.")
    H(2, "subsys", "Sub-slip-systems of titanium", "Titanyumun alt kayma sistemleri")
    P("Dragomir and Ungár [@dragomir2002] give the constants of 11 sub-slip-systems of Ti (@tab:sub): four with "
      "⟨a⟩ = ⅓⟨2-1-10⟩ Burgers vectors (b = 0.295 nm), two with ⟨c⟩ = ⟨0001⟩ (0.468 nm) and five with "
      "⟨c+a⟩ = ⅓⟨2-1-13⟩ (0.553 nm). The program uses the pure-Ti values for α/α′ Ti-6Al-4V. The ⟨c⟩ screw "
      "sub-system S3 is excluded: its contrast is nearly zero and its q values are therefore numerically meaningless.",
      "Dragomir ve Ungár [@dragomir2002], Ti'nin 11 alt kayma sisteminin sabitlerini verir (@tab:sub): ⟨a⟩ = "
      "⅓⟨2-1-10⟩ Burgers vektörlü dört sistem (b = 0,295 nm), ⟨c⟩ = ⟨0001⟩ olan iki sistem (0,468 nm) ve ⟨c+a⟩ = "
      "⅓⟨2-1-13⟩ olan beş sistem (0,553 nm). Program α/α′ Ti-6Al-4V için saf Ti değerlerini kullanır. ⟨c⟩ vida alt "
      "sistemi S3 dışarıda bırakılır: kontrastı neredeyse sıfırdır, bu yüzden q değerleri sayısal olarak anlamsızdır.")
    sub_rows = [[n, tl[v[0]], f"{v[1]:.5g}", f"{v[2]:.5g}", f"{v[3]:.5g}"] for n, v in TI_SUBSYSTEMS.items()]
    TAB("sub", "Average contrast factors of the hk.0 reflections and q parameters of the sub-slip-systems of Ti "
        "[@dragomir2002]. B: basal, Pr: prismatic, Py: pyramidal, E: edge, S: screw.",
        "Ti alt kayma sistemlerinin hk.0 yansımaları için ortalama kontrast faktörleri ve q parametreleri "
        "[@dragomir2002]. B: bazal, Pr: prizmatik, Py: piramidal, E: kenar, S: vida.",
        [t("Sub-system", "Alt sistem"), t("Type", "Tip"), "C̄<sub>hk.0</sub>", "q₁", "q₂"], sub_rows)
    H(2, "mixture", "Mixtures of dislocations and the attainable region", "Dislokasyon karışımları ve ulaşılabilir bölge")
    P("The mean-square strains of independent dislocation populations add, so in @eq:AD the product "
      "$\\rho b^2\\overline{C}$ becomes a sum over the populations i with densities $\\rho_i=f_i\\rho$. Using "
      "@eq:hex for each of them,",
      "Bağımsız dislokasyon popülasyonlarının ortalama kare gerinimleri toplanır; bu yüzden @eq:AD'de "
      "$\\rho b^2\\overline{C}$ çarpımı, yoğunlukları $\\rho_i=f_i\\rho$ olan i popülasyonları üzerinden bir toplama "
      "dönüşür. Her biri için @eq:hex kullanılırsa")
    EQ("mixsum", r"\overline{b^2C}_{hkl}=\sum_i f_i\,b_i^2C_i\left(1+q_1^{(i)}x+q_2^{(i)}x^2\right)\equiv"
                 r"\overline{b^2C}_{hk.0}\left(1+q_1x+q_2x^2\right)")
    P("Comparing the coefficients of 1, x and x² gives",
      "1, x ve x² katsayıları karşılaştırılırsa:")
    EQ("mix", r"\overline{b^2C}_{hk.0}=\sum_i f_ib_i^2C_i,\qquad q_j=\sum_i w_i\,q_j^{(i)},\qquad "
              r"w_i=\frac{f_ib_i^2C_i}{\sum_k f_kb_k^2C_k}")
    P("The weights $w_i$ are non-negative and sum to one, so the measured pair $(q_1,q_2)$ is a convex combination "
      "of the sub-system points of @tab:sub. Conversely, every point of their convex hull is produced by some "
      "mixture. The hull is the <i>attainable region</i> (@fig:burgers a). A measured q outside it cannot be "
      "explained by any population of Ti dislocations; it signals errors in the widths (instrument correction, "
      "overlaps, texture) rather than an unusual microstructure. (@eq:mixsum assumes the same f(η) for all "
      "populations, as all practical methods do.)",
      "$w_i$ ağırlıkları negatif değildir ve toplamları birdir; dolayısıyla ölçülen $(q_1,q_2)$ çifti @tab:sub'deki "
      "alt sistem noktalarının dışbükey bir birleşimidir. Tersine, dışbükey zarflarının her noktası bir karışımla "
      "üretilebilir. Bu zarf <i>ulaşılabilir bölgedir</i> (@fig:burgers a). Bölgenin dışında ölçülen bir q, hiçbir Ti "
      "dislokasyon popülasyonuyla açıklanamaz; olağan dışı bir mikroyapıdan çok genişliklerdeki hatalara (cihaz "
      "düzeltmesi, çakışmalar, doku) işaret eder. (@eq:mixsum, tüm pratik yöntemler gibi, tüm popülasyonlar için "
      "aynı f(η)'yı varsayar.)")

    # =================================================================== 7 mWH
    H(1, "mwh", "Modified Williamson–Hall analysis", "Modifiye Williamson–Hall analizi")
    H(2, "mwhderiv", "From the Wilkens model to the mWH equation", "Wilkens modelinden mWH denklemine")
    P("Expanding the FWHM of the profile of @eq:AD (with a size term) for small $K^2\\overline{C}$, Ungár and "
      "Borbély [@ungar1996] obtained",
      "@eq:AD'deki profilin (bir boyut terimiyle birlikte) FWHM'sini küçük $K^2\\overline{C}$ için açarak Ungár ve "
      "Borbély [@ungar1996] şunu elde etti:")
    EQ("mwh1", r"\Delta K\simeq\frac{0.9}{D}+\left(\frac{\pi M^2b^2}{2}\right)^{1/2}\rho^{1/2}\,K\,\overline{C}^{1/2}"
               r"+O\left(K^2\overline{C}\right)")
    P("where M is a Wilkens-type arrangement constant. In the quadratic form used for line profiles with "
      "comparable size and strain contributions [@ungar2001], and with @eq:hex,",
      "Burada M, Wilkens tipi bir düzen sabitidir. Boyut ve gerinim katkıları benzer büyüklükte olan profiller için "
      "kullanılan ikinci dereceden biçimde [@ungar2001] ve @eq:hex ile:")
    EQ("mwh", r"\Delta K^2=\alpha+\beta\,K^2\left(1+q_1x+q_2x^2\right),\qquad \alpha=\left(\frac{0.9}{D}\right)^2,"
              r"\quad\beta=\frac{\pi M^2}{2}\,\rho\,\overline{b^2C}_{hk.0}")
    P("ΔK is the total FWHM (@eq:olivero) of the instrument-corrected components (@eq:gcorr). @eq:mwh explains why "
      "the classical WH plot of ΔK against K is scattered for dislocated crystals and becomes smooth against "
      "$K\\overline{C}^{1/2}$ (@fig:mwh a). It also shows the limit of the mWH: β contains the product $M^2\\rho$, "
      "so the mWH alone gives ρ only if M is assumed. Its robust output is the shape of the contrast, $q_1$ and "
      "$q_2$, and thereby the Burgers-vector population. α, β, q₁ and q₂ are fitted together.",
      "ΔK, cihazdan arındırılmış bileşenlerin (@eq:gcorr) toplam FWHM'sidir (@eq:olivero). @eq:mwh, dislokasyonlu "
      "kristallerde ΔK'nin K'ye karşı klasik WH grafiğinin neden dağınık olduğunu ve $K\\overline{C}^{1/2}$'ye "
      "karşı neden düzgünleştiğini açıklar (@fig:mwh a). mWH'nin sınırını da gösterir: β, $M^2\\rho$ çarpımını içerir; "
      "bu yüzden mWH tek başına ancak M varsayılırsa ρ verir. Sağlam çıktısı kontrastın biçimi, yani $q_1$ ve $q_2$, "
      "ve bu yoldan Burgers vektörü popülasyonudur. α, β, q₁ ve q₂ birlikte uydurulur.")
    H(2, "mwhcon", "Constrained mWH", "Kısıtlı mWH")
    P("When $q_1$, $q_2$ are fitted freely, noise and systematic width errors often push them outside the "
      "attainable region (@sec:mixture), and the Burgers-vector population then has no physical solution. "
      "AutoDisloc therefore writes the contrast directly as a mixture of the three Burgers types, inserting "
      "@eq:mixsum with the type averages $P_t$, $q_j^t$ of @sec:typeavg into @eq:mwh:",
      "$q_1$, $q_2$ serbest uydurulduğunda gürültü ve sistematik genişlik hataları onları çoğu zaman ulaşılabilir "
      "bölgenin dışına iter (@sec:mixture); o zaman Burgers vektörü popülasyonunun fiziksel bir çözümü kalmaz. Bu "
      "yüzden AutoDisloc kontrastı doğrudan üç Burgers tipinin karışımı olarak yazar; @sec:typeavg'deki tip "
      "ortalamaları $P_t$, $q_j^t$ ile @eq:mixsum'u @eq:mwh'de yerine koyar:")
    EQ("mwhcon", r"\Delta K^2=\alpha+K^2\sum_{t\in\{a,\,c,\,c+a\}}g_t\,P_t\left(1+q_1^{t}x+q_2^{t}x^2\right),"
                 r"\qquad \alpha\geq0,\quad g_t\geq0")
    P("@eq:mwhcon is linear in the four unknowns $(\\alpha,g_a,g_c,g_{c+a})$ with non-negativity constraints, a "
      "convex problem solved exactly by non-negative least squares [@lawson1974]. The fractions are "
      "$h_t=g_t/\\sum g$, and q₁, q₂ follow from @eq:mix; they always lie in the attainable region. If the free "
      "q is already inside the region, both fits give the same result (verified in the tests). If the dislocation "
      "term vanishes (no anisotropic broadening), the program falls back to the free fit.",
      "@eq:mwhcon, negatif olmama kısıtlarıyla dört bilinmeyende $(\\alpha,g_a,g_c,g_{c+a})$ doğrusaldır; negatif "
      "olmayan en küçük karelerle [@lawson1974] tam olarak çözülen dışbükey bir problemdir. Oranlar "
      "$h_t=g_t/\\sum g$'dir; q₁, q₂ @eq:mix'ten çıkar ve her zaman ulaşılabilir bölgededir. Serbest q zaten bölgenin "
      "içindeyse iki uydurma aynı sonucu verir (testlerde doğrulandı). Dislokasyon terimi sıfırlanırsa (anizotrop "
      "genişleme yoksa) program serbest uydurmaya döner.")
    FIG("mwh", "mwh", "Modified Williamson–Hall analysis of the worked example: (a) ΔK against "
        "$K(1+q_1x+q_2x^2)^{1/2}$ with the fit of @eq:mwh; (b) $(\\Delta K^2-\\alpha)/K^2$ against x, the parabola "
        "of @eq:hex.",
        "Uygulamalı örneğin modifiye Williamson–Hall analizi: (a) ΔK'nin $K(1+q_1x+q_2x^2)^{1/2}$'ye karşı grafiği ve "
        "@eq:mwh uydurması; (b) $(\\Delta K^2-\\alpha)/K^2$'nin x'e karşı grafiği, @eq:hex'in parabolü.")
    EX("Constrained mWH: α = «alpha» nm<sup>−2</sup> (D ≈ «D» nm), q₁ = «q1», q₂ = «q2»"
       + (" (true «t_q1», «t_q2»)" if synthetic else "") + ", R² = «mwh_r2». The free fit gives q = («qf1», «qf2»).",
       "Kısıtlı mWH: α = «alpha» nm<sup>−2</sup> (D ≈ «D» nm), q₁ = «q1», q₂ = «q2»"
       + (" (gerçek «t_q1», «t_q2»)" if synthetic else "") + ", R² = «mwh_r2». Serbest uydurma q = («qf1», «qf2») veriyor.")

    # =================================================================== 8 BURGERS
    H(1, "burgers", "Burgers-vector population", "Burgers vektörü popülasyonu")
    H(2, "typeavg", "Type averages", "Tip ortalamaları")
    P("With 10 sub-systems and only two measured numbers, the sub-system fractions are not determined. Dragomir and "
      "Ungár [@dragomir2002] assume that, within each Burgers type t, the sub-systems are equally populated. The "
      "type averages are then",
      "10 alt sistem ve yalnızca iki ölçülen sayıyla alt sistem oranları belirlenemez. Dragomir ve Ungár "
      "[@dragomir2002], her Burgers tipi t içinde alt sistemlerin eşit olasılıklı olduğunu varsayar. Tip ortalamaları "
      "o zaman:")
    EQ("typeavg", r"P_t=\overline{C}_t\,b_t^2,\qquad \overline{C}_t=\frac{1}{n_t}\sum_{i\in t}C_i,\qquad "
                  r"q_j^{t}=\frac{\sum_{i\in t}C_i\,q_j^{(i)}}{\sum_{i\in t}C_i}")
    type_rows = [[tl[k], f"{BURGERS_NM[k]}", f"{P_t[k]:.5f}", f"{T1[k]:.3f}", f"{T2[k]:.3f}"] for k in P_t]
    TAB("types", "Type-averaged constants of @eq:typeavg (S3 excluded).",
        "@eq:typeavg'nin tip ortalamalı sabitleri (S3 hariç).",
        [t("Type", "Tip"), "b (nm)", "P<sub>t</sub> (nm²)", "q₁ᵗ", "q₂ᵗ"], type_rows)
    H(2, "hsolve", "Fractions from the measured q", "Ölçülen q'dan oranlar")
    P("Writing @eq:mix with the three types and multiplying out the denominator gives three linear equations for "
      "the fractions $h_t$:",
      "@eq:mix'i üç tiple yazıp paydayı çarparak açmak, $h_t$ oranları için üç doğrusal denklem verir:")
    EQ("hsys", r"\sum_t h_t\,P_t\left(q_1^{t}-q_1\right)=0,\qquad \sum_t h_t\,P_t\left(q_2^{t}-q_2\right)=0,\qquad "
               r"\sum_t h_t=1")
    P("and $\\overline{b^2C}_{hk.0}=\\sum_t h_tP_t$. The solution is physical only when all $h_t$ lie in [0, 1], that "
      "is, when q is inside the triangle spanned by the three type points. With the constrained mWH this holds by "
      "construction. ρ is inversely proportional to $\\overline{b^2C}_{hk.0}$ (@eq:AD), so its uncertainty enters "
      "ρ directly.",
      "ve $\\overline{b^2C}_{hk.0}=\\sum_t h_tP_t$. Çözüm yalnızca tüm $h_t$ değerleri [0, 1] aralığındaysa, yani q üç "
      "tip noktasının oluşturduğu üçgenin içindeyse fizikseldir. Kısıtlı mWH'de bu kendiliğinden sağlanır. ρ, "
      "$\\overline{b^2C}_{hk.0}$ ile ters orantılı olduğundan (@eq:AD) bunun belirsizliği doğrudan ρ'ya geçer.")
    H(2, "comb40", "The 40-combination method", "40 kombinasyon yöntemi")
    P("An alternative reduction picks one sub-system of each type instead of the type average. Ti has 4 × 2 × 5 = 40 "
      "such combinations; each gives a 3 × 3 system of the form @eq:hsys. The program solves all of them and "
      "reports the mean of the physical solutions (all h in [0, 1]). When q lies outside the attainable region no "
      "combination is physical, and any 'average' of the unphysical rows has no meaning. This explains the "
      "frequent result h⟨a⟩ ≈ 1 of free fits: the nearest attainable point is then the pure ⟨a⟩ corner.",
      "Başka bir indirgeme, tip ortalaması yerine her tipten bir alt sistem seçer. Ti'de böyle 4 × 2 × 5 = 40 "
      "kombinasyon vardır; her biri @eq:hsys biçiminde 3 × 3 bir sistem verir. Program hepsini çözer ve fiziksel "
      "çözümlerin (tüm h değerleri [0, 1] aralığında) ortalamasını raporlar. q ulaşılabilir bölgenin dışındaysa hiçbir "
      "kombinasyon fiziksel değildir ve fiziksel olmayan satırların herhangi bir 'ortalaması' anlamsızdır. Serbest "
      "uydurmalarda sık görülen h⟨a⟩ ≈ 1 sonucunun nedeni budur: en yakın ulaşılabilir nokta o zaman saf ⟨a⟩ köşesidir.")
    H(2, "lprange", "Exact range over all sub-system mixtures", "Tüm alt sistem karışımları üzerinden kesin aralık")
    P("Without the equal-population assumption, the set of sub-system fractions $f_i\\geq0$, $\\sum f_i=1$ that "
      "reproduce the measured q is defined by the linear constraints $\\sum_i f_ib_i^2C_i(q_j^{(i)}-q_j)=0$. The "
      "smallest and largest $\\overline{b^2C}_{hk.0}$ and $h_t$ over this set are therefore linear programs, solved "
      "with the HiGHS solver of SciPy [@virtanen2020]. The range is reported with every result and is used in the "
      "Monte Carlo uncertainty of the Voigt-mWA (@sec:mc).",
      "Eşit popülasyon varsayımı olmadan, ölçülen q'yu üreten $f_i\\geq0$, $\\sum f_i=1$ alt sistem oranları kümesi "
      "$\\sum_i f_ib_i^2C_i(q_j^{(i)}-q_j)=0$ doğrusal kısıtlarıyla tanımlanır. Bu küme üzerindeki en küçük ve en "
      "büyük $\\overline{b^2C}_{hk.0}$ ve $h_t$ bu yüzden doğrusal programlama problemleridir ve SciPy'nin HiGHS "
      "çözücüsüyle [@virtanen2020] çözülür. Aralık her sonuçla raporlanır ve Voigt-mWA'nın Monte Carlo "
      "belirsizliğinde (@sec:mc) kullanılır.")
    FIG("burgers", "burgers", "(a) q₁–q₂ plane: Ti sub-slip-systems (squares), type averages (diamonds) and the "
        "attainable region (@sec:mixture) with the free mWH, constrained mWH and whole-profile values of the worked "
        "example. (b) Burgers-vector fractions from each method.",
        "(a) q₁–q₂ düzlemi: Ti alt kayma sistemleri (kareler), tip ortalamaları (eşkenar dörtgenler) ve ulaşılabilir "
        "bölge (@sec:mixture); uygulamalı örneğin serbest mWH, kısıtlı mWH ve tam profil değerleri. (b) Her yöntemin "
        "verdiği Burgers vektörü oranları.")
    EX("Constrained mWH: h = «pha» / «phc» / «phca» (⟨a⟩/⟨c⟩/⟨c+a⟩), b²C̄<sub>hk.0</sub> = «pb2c» nm² "
       "(range over all sub-system mixtures «pb2cmin»–«pb2cmax» nm²). 40-combination method: «comb_n» physical "
       "solutions for the free q.",
       "Kısıtlı mWH: h = «pha» / «phc» / «phca» (⟨a⟩/⟨c⟩/⟨c+a⟩), b²C̄<sub>hk.0</sub> = «pb2c» nm² (tüm alt sistem "
       "karışımları üzerinden aralık «pb2cmin»–«pb2cmax» nm²). 40 kombinasyon yöntemi: serbest q için «comb_n» "
       "fiziksel çözüm.")

    # =================================================================== 9 Voigt mWA
    H(1, "mwa", "Voigt-based modified Warren–Averbach (comparison)", "Voigt tabanlı modifiye Warren–Averbach (karşılaştırma)")
    H(2, "voigtft", "Fourier coefficients of a Voigt profile", "Voigt profilinin Fourier katsayıları")
    P("In the approach of refs. [@hajyakbary2015; @muiruri2020] the Fourier coefficients of every reflection are not "
      "computed from the measured profile but from its fitted Voigt widths. The cosine transform (@eq:fourier) of a "
      "Lorentzian with FWHM $w_L$ and of a Gaussian with FWHM $w_G$ (both in K units) are standard integrals "
      "[@abramowitz1964]:",
      "[@hajyakbary2015; @muiruri2020] kaynaklarının yaklaşımında her yansımanın Fourier katsayıları ölçülen "
      "profilden değil, uydurulan Voigt genişliklerinden hesaplanır. FWHM'si $w_L$ olan bir Lorentz'in ve FWHM'si "
      "$w_G$ olan bir Gauss'un (ikisi de K biriminde) kosinüs dönüşümleri (@eq:fourier) standart integrallerdir "
      "[@abramowitz1964]:")
    EQ("ftL", r"\int_{-\infty}^{\infty}\frac{w_L/2\pi}{s^2+(w_L/2)^2}\cos(2\pi sL)\,\mathrm{d}s=e^{-\pi w_L|L|}")
    EQ("ftG", r"\int_{-\infty}^{\infty}\frac{2\sqrt{\ln2}}{\sqrt{\pi}\,w_G}e^{-4\ln2\,s^2/w_G^2}\cos(2\pi sL)\,"
              r"\mathrm{d}s=e^{-\pi^2w_G^2L^2/(4\ln2)}")
    P("The Voigt function is their convolution, so its coefficient is the product:",
      "Voigt fonksiyonu ikisinin konvolüsyonudur, dolayısıyla katsayısı çarpımdır:")
    EQ("AV", r"A(L)=\exp\left(-\pi w_LL-\frac{\pi^2}{4\ln2}\,w_G^2L^2\right)")
    P("Written with the integral breadths $\\beta_L=\\pi w_L/2$ and $\\beta_G=w_G\\sqrt{\\pi/(4\\ln2)}$ this is "
      "$\\exp(-2\\beta_LL-\\pi\\beta_G^2L^2)$, the form of Balzar and Ledbetter [@balzar1993].",
      "İntegral genişlikleri $\\beta_L=\\pi w_L/2$ ve $\\beta_G=w_G\\sqrt{\\pi/(4\\ln2)}$ ile yazılınca bu, Balzar ve "
      "Ledbetter'in [@balzar1993] biçimi olan $\\exp(-2\\beta_LL-\\pi\\beta_G^2L^2)$'dir.")
    H(2, "wrongft", "An incorrect form in the literature", "Literatürdeki hatalı bir biçim")
    P("Eq. 23 of ref. [@hajyakbary2015] and Eq. 13 of ref. [@muiruri2020] use instead "
      "$A(L)=\\exp(-L^2w_G^2/2-Lw_L)$. Compared with @eq:AV the Lorentzian exponent is too small by a factor π and "
      "the Gaussian exponent by $\\pi^2/(2\\ln2)\\approx7.1$, so A(L) is overestimated (@fig:voigtft), Y(L) of "
      "@eq:YL is too small and ρ is underestimated. A numerical cosine transform of the Voigt profile agrees with "
      "@eq:AV to better than 0.2 % (automated test). Measured-profile approaches of the same family (e.g. "
      "[@shintani2010; @cong2011]) are not affected.",
      "[@hajyakbary2015] kaynağının Denk. 23'ü ve [@muiruri2020] kaynağının Denk. 13'ü bunun yerine "
      "$A(L)=\\exp(-L^2w_G^2/2-Lw_L)$ kullanır. @eq:AV ile karşılaştırıldığında Lorentz üssü π kat, Gauss üssü "
      "$\\pi^2/(2\\ln2)\\approx7,1$ kat küçüktür; bu yüzden A(L) olduğundan büyük çıkar (@fig:voigtft), @eq:YL'deki "
      "Y(L) küçük kalır ve ρ olduğundan düşük hesaplanır. Voigt profilinin sayısal kosinüs dönüşümü @eq:AV ile %0,2'den "
      "iyi örtüşür (otomatik test). Aynı ailedeki ölçülen profile dayalı yaklaşımlar (ör. [@shintani2010; @cong2011]) "
      "bundan etkilenmez.")
    FIG("voigtft", "voigtft", "Fourier coefficients of the broadest instrument-corrected Voigt profile of the worked "
        "example: numerical cosine transform (points), @eq:AV (blue) and the form of refs. [@hajyakbary2015; "
        "@muiruri2020] (orange).",
        "Uygulamalı örneğin cihazdan arındırılmış en geniş Voigt profilinin Fourier katsayıları: sayısal kosinüs "
        "dönüşümü (noktalar), @eq:AV (mavi) ve [@hajyakbary2015; @muiruri2020] kaynaklarının biçimi (turuncu).", 0.7)
    H(2, "mwaeq", "The mWA equations", "mWA denklemleri")
    P("For L ≪ R<sub>e</sub> the Wilkens function reduces to ln(R<sub>e</sub>/L) (@eq:Re). Taking the logarithm of "
      "@eq:product without the instrument factor and inserting @eq:AD gives the mWA equation of Ungár and Borbély "
      "[@ungar1996]:",
      "L ≪ R<sub>e</sub> için Wilkens fonksiyonu ln(R<sub>e</sub>/L)'ye indirgenir (@eq:Re). Cihaz çarpanı olmadan "
      "@eq:product'ın logaritmasını alıp @eq:AD'yi yerine koymak, Ungár ve Borbély'nin [@ungar1996] mWA denklemini "
      "verir:")
    EQ("mwa", r"\ln A(L)=\ln A^S(L)-\frac{\pi}{2}\,\rho\,L^2\ln\left(\frac{R_e}{L}\right)\,X,\qquad "
              r"X=K^2\,\overline{b^2C}_{hkl}")
    P("At a fixed L the size term is the same for all reflections, so ln A(L) is linear in X across the "
      "reflections. Its slope is",
      "Sabit bir L'de boyut terimi tüm yansımalar için aynıdır; bu yüzden ln A(L), yansımalar boyunca X'te doğrusaldır. "
      "Eğimi:")
    EQ("YL", r"Y(L)=\frac{\partial\ln A(L)}{\partial X}=-\frac{\pi\rho}{2}L^2\ln\left(\frac{R_e}{L}\right)"
             r"\quad\Rightarrow\quad\frac{Y(L)}{L^2}=\frac{\pi\rho}{2}\ln L-\frac{\pi\rho}{2}\ln R_e")
    P("A straight line of $Y/L^2$ against ln L has the slope $s=\\pi\\rho/2$ and the intercept $c=-s\\ln R_e$:",
      "$Y/L^2$'nin ln L'ye karşı doğrusunun eğimi $s=\\pi\\rho/2$, kesişimi $c=-s\\ln R_e$'dir:")
    EQ("rhomwa", r"\rho=\frac{2s}{\pi},\qquad R_e=\exp\left(-\frac{c}{s}\right),\qquad M=R_e\sqrt{\rho}")
    NOTE("ρ is obtained from the slope with the factor 2/π of @eq:rhomwa. X uses the reflection-dependent "
         "$\\overline{b^2C}_{hkl}$ of @eq:hex, which carries the contrast information that the regression in X "
         "relies on.",
         "ρ, eğimden @eq:rhomwa'daki 2/π çarpanıyla elde edilir. X, @eq:hex'teki yansımaya bağlı "
         "$\\overline{b^2C}_{hkl}$'yi kullanır; X'teki regresyonun dayandığı kontrast bilgisi bu değerdedir.")
    P("The program builds A(L) of every reflection from @eq:AV with the corrected widths, chooses L on a 1 nm grid "
      "where A(L) ≥ 0.1 for all reflections and iteratively restricts it to L ≤ R<sub>e</sub>, and applies "
      "@eq:YL and @eq:rhomwa.",
      "Program her yansımanın A(L)'sini düzeltilmiş genişliklerle @eq:AV'den kurar; L'yi tüm yansımalarda "
      "A(L) ≥ 0,1 olan 1 nm'lik bir ızgarada seçer ve yinelemeli olarak L ≤ R<sub>e</sub> ile sınırlar; ardından "
      "@eq:YL ve @eq:rhomwa'yı uygular.")
    H(2, "lsens", "Why the Voigt-based mWA depends on the L range", "Voigt tabanlı mWA neden L aralığına bağlıdır")
    P("Insert @eq:AV into @eq:YL. If the widths of the reflections vary with X as $w_L=w_{L0}+aX$ and "
      "$w_G^2=w_{G0}^2+bX$ (as in the mWH), then",
      "@eq:AV'yi @eq:YL'de yerine koyalım. Yansımaların genişlikleri X ile mWH'deki gibi $w_L=w_{L0}+aX$ ve "
      "$w_G^2=w_{G0}^2+bX$ biçiminde değişiyorsa")
    EQ("lsens", r"\frac{Y(L)}{L^2}=-\frac{\pi a}{L}-\frac{\pi^2b}{4\ln2}\quad\Rightarrow\quad"
                r"\frac{\mathrm{d}(Y/L^2)}{\mathrm{d}\ln L}=\frac{\pi a}{L}")
    P("A Voigt profile contains no $L^2\\ln L$ term at all. The 'slope' of @eq:YL is $\\pi a/L$, evaluated over the "
      "chosen window, so ρ = 2s/π falls roughly as 1/L as the window moves to larger L. The scatter of ρ over "
      "different windows is therefore a model error, not noise. The program reports it with every result (@tab:lsens) "
      "and uses the Voigt-mWA only for comparison.",
      "Bir Voigt profili hiç $L^2\\ln L$ terimi içermez. @eq:YL'deki 'eğim', seçilen pencere üzerinde değerlendirilen "
      "$\\pi a/L$'dir; bu yüzden pencere büyük L'ye kaydıkça ρ = 2s/π kabaca 1/L ile düşer. ρ'nun farklı pencerelerdeki "
      "dağılımı bu nedenle gürültü değil, model hatasıdır. Program bunu her sonuçla raporlar (@tab:lsens) ve "
      "Voigt-mWA'yı yalnızca karşılaştırma için kullanır.")
    sens_rows = [[k, sci(v[0], 2), f"{v[1]:.0f}" if np.isfinite(v[1]) else "–"] for k, v in ex.l_sensitivity.items()]
    TAB("lsens", "Voigt-mWA result of the worked example for fixed L windows.",
        "Uygulamalı örneğin sabit L pencereleri için Voigt-mWA sonucu.",
        [t("L window (nm)", "L penceresi (nm)"), "ρ (m⁻²)", "R<sub>e</sub> (nm)"], sens_rows)
    FIG("mwa", "mwa", "Voigt-based mWA of the worked example: (a) ln A(L) against X for selected L (@eq:mwa); "
        "(b) $Y/L^2$ against ln L (@eq:YL).",
        "Uygulamalı örneğin Voigt tabanlı mWA'sı: (a) seçili L değerleri için ln A(L)'nin X'e karşı grafiği "
        "(@eq:mwa); (b) $Y/L^2$'nin ln L'ye karşı grafiği (@eq:YL).")
    EX("Automatic L range «mwa_L» nm: ρ<sub>mWA</sub> = «mwa_rho» m<sup>−2</sup>, R<sub>e</sub> = «mwa_Re» nm"
       + (". The true value is «t_rho» m<sup>−2</sup>." if synthetic else "."),
       "Otomatik L aralığı «mwa_L» nm: ρ<sub>mWA</sub> = «mwa_rho» m<sup>−2</sup>, R<sub>e</sub> = «mwa_Re» nm"
       + (". Gerçek değer «t_rho» m<sup>−2</sup>." if synthetic else "."))

    # =================================================================== 10 WHOLE PROFILE
    H(1, "wp", "Wilkens whole-profile fit (main result)", "Wilkens tam profil uydurması (ana sonuç)")
    P("The whole-profile fit removes the two weak points of the mWA: it uses the full Wilkens function instead of "
      "its logarithmic limit, and it fits the measured intensities instead of Fourier coefficients reconstructed "
      "from Voigt widths. The model is that of CMWP [@ungar2001; @ribarik2001; @ribarik2004].",
      "Tam profil uydurması mWA'nın iki zayıf noktasını ortadan kaldırır: logaritmik limit yerine tam Wilkens "
      "fonksiyonunu kullanır ve Voigt genişliklerinden yeniden kurulmuş Fourier katsayıları yerine ölçülen "
      "şiddetleri uydurur. Model CMWP'ninkidir [@ungar2001; @ribarik2001; @ribarik2004].")
    H(2, "size", "Size: log-normal spheres", "Boyut: log-normal küreler")
    P("For a spherical crystallite of diameter D, the fraction of cell pairs a distance L apart that lie inside the "
      "crystallite (its common volume with a copy shifted by L, divided by its volume) is",
      "D çaplı küresel bir kristalitte, birbirinden L uzaklıktaki hücre çiftlerinden kristalitin içinde kalanların "
      "oranı (L kadar kaydırılmış kopyasıyla ortak hacminin kendi hacmine oranı):")
    EQ("sphere", r"v\left(\frac{L}{D}\right)=1-\frac{3}{2}\frac{L}{D}+\frac{1}{2}\left(\frac{L}{D}\right)^3,\qquad L\leq D")
    P("and zero for L > D. Each crystallite scatters in proportion to its volume ($\\propto D^3$), so the size "
      "coefficient of a population with the diameter distribution g(D) is the volume-weighted average",
      "ve L > D için sıfırdır. Her kristalit hacmiyle ($\\propto D^3$) orantılı saçılma yapar; bu yüzden çap dağılımı "
      "g(D) olan bir popülasyonun boyut katsayısı hacim ağırlıklı ortalamadır:")
    EQ("AS", r"A^S(L)=\frac{\int_0^{\infty}D^3g(D)\,v(L/D)\,\mathrm{d}D}{\int_0^{\infty}D^3g(D)\,\mathrm{d}D},\qquad "
             r"g(D)=\frac{1}{\sqrt{2\pi}\,\sigma D}\exp\left[-\frac{\ln^2(D/m)}{2\sigma^2}\right]")
    P("For a log-normal g(D) with median m, $D^3g(D)$ is again log-normal with median $me^{3\\sigma^2}$, so the "
      "integral is evaluated with 48-point Gauss–Hermite quadrature at $D_k=m\\exp(3\\sigma^2+\\sigma z_k)$. The "
      "area- and volume-weighted mean diameters follow from the moments $\\langle D^n\\rangle=m^ne^{n^2\\sigma^2/2}$:",
      "Medyanı m olan log-normal bir g(D) için $D^3g(D)$ yine medyanı $me^{3\\sigma^2}$ olan bir log-normaldir; "
      "bu yüzden integral $D_k=m\\exp(3\\sigma^2+\\sigma z_k)$ noktalarında 48 noktalı Gauss–Hermite kuadratürüyle "
      "hesaplanır. Alan ve hacim ağırlıklı ortalama çaplar $\\langle D^n\\rangle=m^ne^{n^2\\sigma^2/2}$ "
      "momentlerinden çıkar:")
    EQ("Dmean", r"\langle D\rangle_{area}=\frac{\langle D^3\rangle}{\langle D^2\rangle}=me^{2.5\sigma^2},\qquad "
                r"\langle D\rangle_{vol}=\frac{\langle D^4\rangle}{\langle D^3\rangle}=me^{3.5\sigma^2}")
    H(2, "wpmodel", "Dislocation and instrument factors", "Dislokasyon ve cihaz çarpanları")
    P("$A^D$ is @eq:AD with the full Wilkens function and the contrast of the Burgers-type mixture,",
      "$A^D$, tam Wilkens fonksiyonu ve Burgers tipi karışımının kontrastıyla @eq:AD'dir:")
    EQ("b2cmix", r"\overline{b^2C}_{hkl}(\mathbf{h})=\sum_t h_tP_t\left(1+q_1^tx+q_2^tx^2\right),\qquad "
                 r"R_e=2.877\,\frac{M^*}{\sqrt{\rho}}")
    P("and $A^I$ is @eq:AI evaluated at the K of each reflection. The physical model thus has six global "
      "parameters: ρ, M*, m, σ and two independent Burgers-type fractions.",
      "$A^I$ ise her yansımanın K değerinde hesaplanan @eq:AI'dır. Fiziksel modelin böylece altı genel parametresi "
      "vardır: ρ, M*, m, σ ve iki bağımsız Burgers tipi oranı.")
    H(2, "synth", "Profile synthesis", "Profil sentezi")
    P("For reflection j with Kα1 position $2\\theta_j$ and $K_j=2\\sin\\theta_j/\\lambda_1$, the intensity at a data "
      "point 2θ is",
      "Kα1 konumu $2\\theta_j$ ve $K_j=2\\sin\\theta_j/\\lambda_1$ olan j yansıması için bir 2θ veri noktasındaki şiddet:")
    EQ("synth", r"y_j(2\theta)=A_j\left[I_j(s_1)+r\,I_j(s_2)\right]\frac{\mathrm{d}s}{\mathrm{d}(2\theta)},\qquad "
                r"s_k=\frac{2\sin\theta}{\lambda_k}-K_j,\qquad \frac{\mathrm{d}s}{\mathrm{d}(2\theta)}=\frac{\pi}{180}\,"
                r"\frac{\cos\theta}{\lambda_1}")
    P("where $I_j(s)$ is @eq:fourier with $A=A^SA^DA^I$, evaluated by the trapezoidal rule on L = 0–1500 nm in 1 nm "
      "steps. The instrument factor guarantees that A(L) has vanished long before 1500 nm. The discrete cosine sum "
      "is periodic in s with period 1/ΔL = 1 nm⁻¹; the profile is therefore evaluated only for |s| < 0.4 nm⁻¹, where "
      "the periodic images are negligible. (Evaluating the whole 2θ range produced spurious peaks during "
      "development; the restriction removes them.)",
      "Burada $I_j(s)$, $A=A^SA^DA^I$ ile @eq:fourier'dir ve L = 0–1500 nm aralığında 1 nm adımla yamuk kuralıyla "
      "hesaplanır. Cihaz çarpanı A(L)'nin 1500 nm'den çok önce sönmesini garanti eder. Ayrık kosinüs toplamı s'de "
      "1/ΔL = 1 nm⁻¹ periyotlu periyodiktir; bu yüzden profil yalnızca periyodik görüntülerin ihmal edilebildiği "
      "|s| < 0,4 nm⁻¹ aralığında hesaplanır. (Geliştirme sırasında tüm 2θ aralığının hesaplanması sahte pikler "
      "üretti; bu sınırlama onları ortadan kaldırır.)")
    H(2, "wpfit", "Parameters and objective", "Parametreler ve amaç fonksiyonu")
    P("The fitted parameters are $\\log_{10}\\rho$, $\\log_{10}M^*$ (bounded to 0.5–10, @sec:ident), "
      "$\\log_{10}m$, σ, two softmax variables $u_1,u_2$ with $\\mathbf{h}=(1,e^{u_1},e^{u_2})/(1+e^{u_1}+e^{u_2})$ "
      "(which keeps $h_t\\geq0$, $\\sum h_t=1$ without constraints), the position and area of every reflection and a "
      "linear background per window. Reflections that are not analysed (β, 20.0, 20.2) are free Voigt doublets. "
      "The objective is the χ² of @eq:chi2 over all windows, minimised by the bounded trust-region reflective "
      "algorithm [@branch1999; @virtanen2020] from three starting densities (10<sup>14</sup>, 10<sup>15</sup>, "
      "10<sup>16</sup> m<sup>−2</sup>); the best fit is kept. Start values of positions, areas and background come "
      "from the Voigt fits of @sec:peaks. The goodness of fit is χ²/ν with ν = N − (number of free parameters).",
      "Uydurulan parametreler: $\\log_{10}\\rho$, $\\log_{10}M^*$ (0,5–10 ile sınırlı, @sec:ident), $\\log_{10}m$, σ, "
      "$\\mathbf{h}=(1,e^{u_1},e^{u_2})/(1+e^{u_1}+e^{u_2})$ olan iki softmax değişkeni $u_1,u_2$ (kısıt "
      "gerektirmeden $h_t\\geq0$, $\\sum h_t=1$ sağlar), her yansımanın konumu ve alanı ve her pencere için doğrusal "
      "bir zemin. Analiz edilmeyen yansımalar (β, 20.0, 20.2) serbest Voigt ikilileridir. Amaç fonksiyonu tüm "
      "pencereler üzerinden @eq:chi2'deki χ²'dir; sınırlı güven bölgesi yansıtmalı algoritmayla [@branch1999; "
      "@virtanen2020] üç başlangıç yoğunluğundan (10<sup>14</sup>, 10<sup>15</sup>, 10<sup>16</sup> m<sup>−2</sup>) "
      "en küçüklenir; en iyi uydurma alınır. Konum, alan ve zeminin başlangıç değerleri @sec:peaks'teki Voigt "
      "uydurmalarından gelir. Uydurma kalitesi χ²/ν'dür; ν = N − (serbest parametre sayısı).")
    H(2, "ident", "When ρ and M* cannot be separated", "ρ ile M* ne zaman ayrılamaz")
    P("For η ≫ 1, @eq:f3 gives $f\\to512/(90\\pi\\eta)$, so $L^2f\\to(512/90\\pi)R_e^*L$ and @eq:AD becomes",
      "η ≫ 1 için @eq:f3, $f\\to512/(90\\pi\\eta)$ verir; böylece $L^2f\\to(512/90\\pi)R_e^*L$ olur ve @eq:AD şu hâli alır:")
    EQ("degenerate", r"A^D(L)\to\exp\left(-\frac{256}{90}\,\rho R_e^*\,b^2C\,K^2L\right)="
                     r"\exp\left(-\frac{256}{90}\,M^*\sqrt{\rho}\,b^2C\,K^2L\right)")
    P("This is the Fourier coefficient of a Lorentzian whose width depends only on $M^*\\sqrt{\\rho}$. When "
      "R<sub>e</sub>* is small compared with the L range that carries the profile (small M*, or a weak broadening "
      "that only the large-L region resolves), ρ and M* are therefore not separately determined; the fit slides "
      "along $M^*\\sqrt{\\rho}=$ const. M* is bounded to 0.5–10 for this reason, and @sec:unc describes how such "
      "cases are reported.",
      "Bu, genişliği yalnızca $M^*\\sqrt{\\rho}$'ya bağlı bir Lorentz'in Fourier katsayısıdır. R<sub>e</sub>*, "
      "profili taşıyan L aralığına göre küçükse (küçük M* ya da yalnızca büyük-L bölgesinin çözebildiği zayıf bir "
      "genişleme), ρ ile M* bu yüzden ayrı ayrı belirlenemez; uydurma $M^*\\sqrt{\\rho}=$ sabit doğrusu boyunca kayar. "
      "M* bu nedenle 0,5–10 ile sınırlanır; @sec:unc böyle durumların nasıl raporlandığını anlatır.")
    FIG("fourier", "fourier", "Size and dislocation Fourier factors fitted for the reflection with the highest K of "
        "the worked example (@eq:AS, @eq:AD).",
        "Uygulamalı örnekte en yüksek K'li yansıma için uydurulan boyut ve dislokasyon Fourier çarpanları "
        "(@eq:AS, @eq:AD).", 0.7)
    FIG("wp", "wp", "Whole-profile fit of the worked example: measured points, Wilkens model and difference in every "
        "window.",
        "Uygulamalı örneğin tam profil uydurması: her pencerede ölçülen noktalar, Wilkens modeli ve fark.")
    if synthetic:
        rows = [["ρ (m⁻²)", "«t_rho»", "«rho»"], ["M*", "«t_M»", "«Mstar»"], ["h⟨a⟩", "«t_ha»", "«ha»"],
                ["b²C̄<sub>hk.0</sub> (nm²)", f"{truth['b2C_hk0_nm2']:.4f}", "«b2c»"],
                [t("size median m (nm)", "boyut medyanı m (nm)"), "«t_m»", "«m_nm»"], ["σ", "«t_sig»", "«sig»"]]
        TAB("truth", "Worked example: true parameters and whole-profile result. 95 % interval of ρ: «lo»–«hi» m⁻² "
            "(«interval_method»).",
            "Uygulamalı örnek: gerçek parametreler ve tam profil sonucu. ρ'nun %95 aralığı: «lo»–«hi» m⁻² "
            "(«interval_method»).",
            [t("Parameter", "Parametre"), t("true", "gerçek"), t("fitted", "bulunan")], rows)
    EX("ρ = «rho» m<sup>−2</sup> (95 %: «lo»–«hi»), M* = «Mstar» (R<sub>e</sub>* = «Restar» nm), h = «ha» / «hc» / "
       "«hca», b²C̄<sub>hk.0</sub> = «b2c» nm², m = «m_nm» nm, σ = «sig»; N = «npts» points, «nfree» free "
       "parameters, χ²/ν = «gof», Rwp = «rwp» %.",
       "ρ = «rho» m<sup>−2</sup> (%95: «lo»–«hi»), M* = «Mstar» (R<sub>e</sub>* = «Restar» nm), h = «ha» / «hc» / "
       "«hca», b²C̄<sub>hk.0</sub> = «b2c» nm², m = «m_nm» nm, σ = «sig»; N = «npts» nokta, «nfree» serbest "
       "parametre, χ²/ν = «gof», Rwp = %«rwp».")

    # =================================================================== 11 UNCERTAINTY
    H(1, "unc", "Uncertainty and detection limit", "Belirsizlik ve algılama sınırı")
    H(2, "jac", "Well-conditioned fits: Jacobian interval", "İyi koşullu uydurmalar: Jacobian aralığı")
    P("Near the minimum the covariance of the parameters is approximated from the Jacobian J of the weighted "
      "residuals,",
      "Minimum yakınında parametrelerin kovaryansı, ağırlıklı artıkların Jacobian'ı J'den yaklaşık olarak bulunur:")
    EQ("cov", r"\mathrm{Cov}(\mathbf{p})\approx s^2\left(\mathbf{J}^{T}\mathbf{J}\right)^{-1},\qquad "
              r"s^2=\frac{\chi^2_{min}}{\nu},\qquad \log_{10}\rho\pm1.96\,\sigma_{\log\rho}")
    P("Scaling by $s^2$ inflates the errors when the model explains the data less well than counting statistics "
      "would allow. The Jacobian interval is used when neither ρ nor M* is at a bound and $\\sigma_{\\log\\rho}<0.2$.",
      "$s^2$ ile ölçekleme, model veriyi sayım istatistiğinin izin verdiğinden daha kötü açıklıyorsa hataları büyütür. "
      "Jacobian aralığı, ne ρ ne M* sınırdayken ve $\\sigma_{\\log\\rho}<0,2$ iken kullanılır.")
    H(2, "band", "Weak broadening: fixed M* with a band", "Zayıf genişleme: bant ile sabit M*")
    P("Otherwise ρ and M* are not separable (@sec:ident). M* is then fixed at a reference value (user adjustable, "
      "option <i>Reference M*</i>), and the reported interval is the union of the statistical intervals obtained "
      "with the reference value and with the ends of the band M* = 1.5 and 4.0. The result therefore carries the "
      "arrangement assumption explicitly: a larger assumed M* gives a smaller ρ. The default reference value 2.64 "
      "is only the geometric mean of the free-fit M* (2.17 and 3.21) of two well-conditioned samples measured "
      "during the development of the program with the example instrument model; it is not a universal constant. "
      "Users should set a value appropriate for their material and instrument, for example from free fits of "
      "their own well-conditioned samples. All M* values here are in the program's convention (@sec:ffunc; "
      "M*<sub>CMWP</sub> = M*/2.568). The program states the fixed value and this dependence in its warnings.",
      "Aksi hâlde ρ ile M* ayrılamaz (@sec:ident). M* o zaman bir referans değere sabitlenir (kullanıcı "
      "değiştirebilir, <i>Referans M*</i> seçeneği) ve raporlanan aralık, referans değerle ve bandın uçları "
      "M* = 1,5 ve 4,0 ile elde edilen istatistik aralıkların birleşimidir. Sonuç böylece düzen varsayımını açıkça "
      "taşır: varsayılan M* büyüdükçe ρ küçülür. Varsayılan referans değer 2,64, programın geliştirilmesi sırasında "
      "örnek cihaz modeliyle ölçülmüş iyi koşullu iki numunenin serbest uydurma M* değerlerinin (2,17 ve 3,21) "
      "geometrik ortalamasından ibarettir; evrensel bir sabit değildir. Kullanıcı malzemesine ve cihazına uygun bir "
      "değer girmelidir, ör. kendi iyi koşullu numunelerinin serbest uydurmalarından. Buradaki tüm M* değerleri "
      "programın tanımıyladır (@sec:ffunc; M*<sub>CMWP</sub> = M*/2,568). Program sabitlenen değeri ve bu "
      "bağımlılığı uyarılarında belirtir.")
    H(2, "pl", "Below the detection limit: profile likelihood", "Algılama sınırının altında: profil olabilirliği")
    P("If ρ goes to its lower bound, the dislocation broadening is not detected and only an upper limit is "
      "meaningful. The profile likelihood fixes ρ on a grid and refits all other parameters at every point, each fit "
      "starting from its neighbour so that the scan follows one minimum:",
      "ρ alt sınırına giderse dislokasyon genişlemesi algılanmamıştır ve yalnızca bir üst sınır anlamlıdır. Profil "
      "olabilirliği ρ'yu bir ızgarada sabitler ve her noktada diğer tüm parametreleri yeniden uydurur; tarama tek bir "
      "minimumu izlesin diye her uydurma komşusundan başlar:")
    EQ("pl", r"\chi^2_p(\rho)=\min_{\mathbf{p}\setminus\rho}\chi^2(\mathbf{p}),\qquad "
             r"\chi^2_p(\rho_{95})-\chi^2_{min}=3.84\,\frac{\chi^2_{min}}{\nu}")
    P("By Wilks' theorem [@wilks1938] $\\Delta\\chi^2$ follows a χ² distribution with one degree of freedom, whose "
      "95 % point is 3.84; the factor $\\chi^2_{min}/\\nu$ applies the same scaling as @eq:cov. The scan is made "
      "with M* = 1.5, the end of the band that broadens least per unit ρ, so the upper limit is conservative.",
      "Wilks teoremine [@wilks1938] göre $\\Delta\\chi^2$ bir serbestlik dereceli χ² dağılımına uyar; bunun %95 "
      "noktası 3,84'tür. $\\chi^2_{min}/\\nu$ çarpanı @eq:cov'dakiyle aynı ölçeklemeyi uygular. Tarama, birim ρ başına "
      "en az genişleten bant ucu olan M* = 1,5 ile yapılır; böylece üst sınır temkinlidir.")
    FIG("pl", "pl", "Profile likelihood of ρ for sample «up»"
        + (" (synthetic, true ρ = 10<sup>11</sup> m<sup>−2</sup>)" if synthetic else "")
        + ". The 95 % upper limit is where the curve crosses the threshold: ρ < «upper» m<sup>−2</sup>.",
        "«up» numunesi için ρ'nun profil olabilirliği"
        + (" (sentetik, gerçek ρ = 10<sup>11</sup> m<sup>−2</sup>)" if synthetic else "")
        + ". %95 üst sınır, eğrinin eşiği kestiği yerdir: ρ < «upper» m<sup>−2</sup>.", 0.62)
    H(2, "mc", "Monte Carlo uncertainty of the Voigt-mWA", "Voigt-mWA'nın Monte Carlo belirsizliği")
    P("For the comparison route, the widths are perturbed with their standard errors and $\\overline{b^2C}_{hk.0}$ "
      "is drawn uniformly from its exact range (@sec:lprange); the 16th and 84th percentiles of ρ over the draws are "
      "reported together with the L-range band of @sec:lsens.",
      "Karşılaştırma yolunda genişlikler standart hatalarıyla bozulur ve $\\overline{b^2C}_{hk.0}$ kesin aralığından "
      "(@sec:lprange) düzgün dağılımla çekilir; çekimler üzerinden ρ'nun 16. ve 84. yüzdelikleri, @sec:lsens'teki "
      "L-aralığı bandıyla birlikte raporlanır.")

    # =================================================================== 12 VALIDITY
    H(1, "valid", "Validity checks", "Geçerlilik denetimleri")
    P("Every result is accompanied by warnings that the program derives from the data:",
      "Her sonuç, programın veriden türettiği uyarılarla birlikte verilir:")
    UL(["fewer than five usable reflections: the analysis is invalid;",
        "a sample/instrument width ratio below 1.5: the reflection is close to the detection limit; for three or "
        "more reflections the sample is flagged as being at the detection limit;",
        "a component narrower than the instrument (set to zero in @eq:gcorr), or reflections outside the K range of "
        "the standard;",
        "mWH R² < 0.8, or a free q outside the attainable region;",
        "Voigt-mWA: non-positive slope s, positive Y(L), M outside 0.5–10, or a strong L-range dependence;",
        "whole profile: a parameter at its bound, or χ²/ν > 3 (the model misses features beyond counting "
        "statistics, e.g. phase transformation, stacking faults or texture);",
        "texture: a Harris index outside 0.5–2."],
       ["kullanılabilir yansıma sayısı beşten azsa analiz geçersizdir;",
        "numune/cihaz genişlik oranı 1,5'in altındaysa yansıma algılama sınırına yakındır; üç veya daha fazla "
        "yansımada böyleyse numune algılama sınırında olarak işaretlenir;",
        "cihazdan dar bir bileşen (@eq:gcorr'de sıfırlanır) ya da standardın K aralığı dışındaki yansımalar;",
        "mWH R² < 0,8 ya da ulaşılabilir bölgenin dışında kalan serbest q;",
        "Voigt-mWA: pozitif olmayan eğim s, pozitif Y(L), 0,5–10 dışında M ya da güçlü L-aralığı bağımlılığı;",
        "tam profil: sınıra dayanan bir parametre ya da χ²/ν > 3 (model sayım istatistiğinin ötesinde özellikleri "
        "kaçırıyor, ör. faz dönüşümü, istif hataları ya da doku);",
        "doku: 0,5–2 dışında bir Harris katsayısı."])
    P("The Harris texture index [@harris1952] compares the integrated intensity $I_{hkl}$ with the intensity "
      "$I^0_{hkl}$ of an untextured powder (ICDD):",
      "Harris doku katsayısı [@harris1952], integral şiddet $I_{hkl}$'yi dokusuz bir tozun şiddeti $I^0_{hkl}$ ile "
      "(ICDD) karşılaştırır:")
    EQ("harris", r"T_{hkl}=\frac{I_{hkl}/I^0_{hkl}}{\frac{1}{N}\sum_{N}I_{hkl}/I^0_{hkl}}")
    P("T = 1 for a random polycrystal. The average contrast factors of @sec:contrast assume random orientation, so "
      "strongly textured reflections reduce the reliability of q and of the Burgers-vector population; the texture "
      "should then be checked with EBSD or pole figures.",
      "Rastgele yönelimli bir çok kristal için T = 1'dir. @sec:contrast'taki ortalama kontrast faktörleri rastgele "
      "yönelim varsayar; güçlü dokulu yansımalar q'nun ve Burgers vektörü popülasyonunun güvenilirliğini azaltır. "
      "Bu durumda doku EBSD ya da kutup figürleriyle denetlenmelidir.")

    # =================================================================== 13 VALIDATION
    H(1, "validation", "Validation", "Doğrulama")
    H(2, "litval", "Reproduction of published numbers", "Yayımlanmış sayıların yeniden üretimi")
    P("Each item of @tab:lit is repeated by an automated test (<code>python -m pytest tests</code>).",
      "@tab:lit'teki her madde otomatik bir testle tekrarlanır (<code>python -m pytest tests</code>).")
    lit = [
        [t("Dragomir & Ungár [@dragomir2002], ECAP Ti", "Dragomir ve Ungár [@dragomir2002], ECAP Ti"),
         t("q₁ = −0.05, q₂ = 0.18 → h, b²C̄", "q₁ = −0,05, q₂ = 0,18 → h, b²C̄"),
         t("h = 0.73/0.23/0.05 (paper 0.75 ± 0.10 / 0.20 ± 0.05 / 0.05 ± 0.03); b²C̄ = 0.0220 nm² (paper 0.0222) ✓",
           "h = 0,73/0,23/0,05 (makale 0,75 ± 0,10 / 0,20 ± 0,05 / 0,05 ± 0,03); b²C̄ = 0,0220 nm² (makale 0,0222) ✓")],
        [t("Muiruri et al. [@muiruri2020], Table 4", "Muiruri ve ark. [@muiruri2020], Tablo 4"),
         "h → b²C̄", t("all five values to four digits ✓; the published h are inconsistent with the published q",
                       "beş değerin hepsi dört basamak ✓; yayımlanan h değerleri yayımlanan q değerleriyle tutarsız")],
        [t("Combination method, one sub-system per Burgers type [@dragomir2002]", "Kombinasyon yöntemi, Burgers tipi başına bir alt-sistem [@dragomir2002]"),
         t("40 combinations, Eqs. 11–13", "40 kombinasyon, Denk. 11–13"),
         t("every solution satisfies Σh = 1 and reproduces q₁, q₂ ✓", "her çözüm Σh = 1'i sağlar ve q₁, q₂'yi geri üretir ✓")],
        [t("Shintani et al. [@shintani2010], Mg alloy", "Shintani ve ark. [@shintani2010], Mg alaşımı"),
         t("6 FWHM → α, D", "6 FWHM → α, D"),
         t("α = 4.44×10⁻⁵ nm⁻² (paper 4.29×10⁻⁵) only with ΔK = 2cosθ·Δ(2θ)/λ", "α = 4,44×10⁻⁵ nm⁻² (makale 4,29×10⁻⁵) yalnızca ΔK = 2cosθ·Δ(2θ)/λ ile")],
        [t("Voigt Fourier transform", "Voigt Fourier dönüşümü"), t("numerical cosine transform", "sayısal kosinüs dönüşümü"),
         t("@eq:AV within 0.2 % ✓", "@eq:AV %0,2 içinde ✓")],
        [t("Constrained vs. free mWH", "Kısıtlı ve serbest mWH"), t("q inside the attainable region", "q ulaşılabilir bölgenin içinde"),
         t("identical results ✓", "aynı sonuç ✓")],
    ]
    TAB("lit", "Reproduction of published results.", "Yayımlanmış sonuçların yeniden üretimi.",
        [t("Source", "Kaynak"), t("Reproduced", "Yeniden üretilen"), t("Result", "Sonuç")], lit)
    H(2, "synval", "Synthetic recovery", "Sentetik geri kazanım")
    P("Ti-6Al-4V patterns with known ρ, M*, Burgers-vector population and size distribution were generated with the "
      "model of @sec:wp, the example instrument model, Cu Kα1+Kα2 and Poisson noise, and analysed like measured "
      "data (@tab:syn, @fig:syn).",
      "Bilinen ρ, M*, Burgers vektörü popülasyonu ve boyut dağılımına sahip Ti-6Al-4V desenleri @sec:wp'deki modelle, "
      "örnek cihaz modeli, Cu Kα1+Kα2 ve Poisson gürültüsüyle üretildi ve ölçülmüş veri gibi analiz edildi "
      "(@tab:syn, @fig:syn).")
    syn_rows = [[sci(r["rho"], 1), sci(r["rho_fit"], 2), f"{100 * (r['rho_fit'] / r['rho'] - 1):+.0f} %",
                 f"{r['M']:.2f} → {r['M_fit']:.2f}", f"{r['ha']:.2f} → {r['ha_fit']:.2f}",
                 f"{r['m']:.0f} → {r['m_fit']:.0f}", f"{r['gof']:.2f}"] for r in data["syn"]]
    TAB("syn", "Synthetic recovery with the whole-profile fit (true → fitted).",
        "Tam profil uydurmasıyla sentetik geri kazanım (gerçek → bulunan).",
        [t("true ρ (m⁻²)", "gerçek ρ (m⁻²)"), t("fitted ρ", "bulunan ρ"), t("deviation", "sapma"), "M*", "h⟨a⟩",
         "m (nm)", "χ²/ν"], syn_rows)
    FIG("syn", "syn", "True and fitted dislocation density of the synthetic patterns of @tab:syn.",
        "@tab:syn'deki sentetik desenlerin gerçek ve bulunan dislokasyon yoğunluğu.", 0.6)
    devs = ", ".join(f"{100 * (r['rho_fit'] / r['rho'] - 1):+.0f} %" for r in data["syn"])
    V["syn_devs"] = devs
    P("The deviations of ρ are «syn_devs». The largest occurs for the weakest broadening, where M* and the size "
      "parameters are partly correlated with ρ (@sec:ident) and scatter more. For reference, a neutron eCMWP study of SLM Ti-6Al-4V reported "
      "ρ = (2.4 ± 0.3)×10<sup>15</sup> m<sup>−2</sup> with 85 % ⟨a⟩ dislocations [@cottam2019]. A direct comparison "
      "with the CMWP program on identical data has not yet been made.",
      "ρ'daki sapmalar «syn_devs». En büyüğü en zayıf genişlemede görülür; orada M* ve boyut parametreleri ρ ile "
      "kısmen ilişkilidir (@sec:ident) ve daha çok dağılır. Karşılaştırma için: SLM Ti-6Al-4V üzerine nötron eCMWP çalışması ρ = (2,4 ± 0,3)×10<sup>15</sup> "
      "m<sup>−2</sup> ve %85 ⟨a⟩ dislokasyonu raporladı [@cottam2019]. Aynı veri üzerinde CMWP programıyla doğrudan "
      "karşılaştırma henüz yapılmadı.")

    # =================================================================== 14 RESULTS
    if synthetic:
        H(2, "batch", "Batch output", "Toplu çıktı")
        P("@fig:compare is the summary chart of the program for the two synthetic examples: A with a well-defined ρ "
          "and B below the detection limit, reported as an upper limit.",
          "@fig:compare, programın iki sentetik örnek için özet grafiğidir: ρ'su iyi belirlenen A ve algılama sınırının "
          "altında kalıp üst sınır olarak raporlanan B.")
        FIG("compare", "compare", "Dislocation density of the synthetic examples (log scale). Filled points: whole-profile "
            "result with 95 % interval; arrow: 95 % upper limit; open circles: Voigt-mWA.",
            "Sentetik örneklerin dislokasyon yoğunluğu (log ölçek). Dolu noktalar: %95 aralığıyla tam profil sonucu; "
            "ok: %95 üst sınır; boş daireler: Voigt-mWA.", 0.55)
    else:
        H(1, "results", "Application: measured samples", "Uygulama: ölçülmüş numuneler")
        rr = []
        for r in res:
            s = r.summary()
            rr.append([r.sample, f"<b>{s['rho_text']}</b>", str(s["interval_method"]), num(s["M_star"]),
                       f"{num(s['h_a'])} / {num(s['h_c'])} / {num(s['h_ca'])}", num(s["chi2_dof"]),
                       sci(s["mwa_rho"], 1)])
        TAB("ht", "Results of the measured samples.", "Ölçülmüş numunelerin sonuçları.",
            [t("Sample", "Numune"), t("ρ (m⁻²) and 95 % interval", "ρ (m⁻²) ve %95 aralık"),
             t("Interval method", "Aralık yöntemi"), "M*", "h ⟨a⟩/⟨c⟩/⟨c+a⟩", "χ²/ν", "Voigt-mWA"], rr)
        FIG("compare", "compare", "Dislocation density of the measured samples (log scale). Filled points: "
            "whole-profile result with 95 % interval; arrow: 95 % upper limit; open circles: Voigt-mWA.",
            "Ölçülmüş numunelerin dislokasyon yoğunluğu (log ölçek). Dolu noktalar: %95 aralığıyla tam profil "
            "sonucu; ok: %95 üst sınır; boş daireler: Voigt-mWA.", 0.55)

    # =================================================================== 15 LIMITATIONS
    H(1, "limits", "Limitations", "Sınırlamalar")
    UL(["The contrast constants are those of pure Ti [@dragomir2002]; the elastic constants of the alloy and of α′ "
        "martensite differ somewhat.",
        "The average contrast factor assumes an untextured polycrystal (@sec:valid).",
        "Planar faults, twin boundaries and the β phase are not part of the physical model; their broadening is "
        "absorbed into the size and dislocation parameters, and χ²/ν signals it.",
        "For weak broadening ρ and M* are not separable (@sec:ident); the result then depends on the assumed M* "
        "and its band, which are stated with the result. The default reference M* = 2.64 is not a universal "
        "constant (@sec:band); set it for the material and instrument.",
        "M* and R_e* are reported in the program's convention; M*<sub>CMWP</sub> = M*/2.568 (@sec:ffunc).",
        "The fit weights (1/√y), χ²/ν and the error intervals assume raw counts; the program warns when the "
        "intensities are not raw counts (counts per second, normalised or processed data).",
        "The quality of the instrument model limits the detection limit. A line standard measured with a fine step "
        "(≤ 0.005°) and without Kα2 stripping, preferably LaB6 (NIST SRM 660), is recommended.",
        "A direct comparison with the CMWP program on identical data is still to be made."],
       ["Kontrast sabitleri saf Ti içindir [@dragomir2002]; alaşımın ve α′ martensitin elastik sabitleri bir miktar "
        "farklıdır.",
        "Ortalama kontrast faktörü dokusuz bir çok kristal varsayar (@sec:valid).",
        "Düzlemsel kusurlar, ikiz sınırları ve β fazı fiziksel modelin parçası değildir; bunların genişlemesi boyut "
        "ve dislokasyon parametrelerine yansır ve χ²/ν bunu gösterir.",
        "Zayıf genişlemede ρ ile M* ayrılamaz (@sec:ident); sonuç o zaman varsayılan M*'a ve bandına bağlıdır ve "
        "bunlar sonuçla birlikte belirtilir. Varsayılan referans M* = 2,64 evrensel bir sabit değildir (@sec:band); "
        "malzemeye ve cihaza göre ayarlanmalıdır.",
        "M* ve R_e* programın tanımıyla raporlanır; M*<sub>CMWP</sub> = M*/2,568 (@sec:ffunc).",
        "Uydurma ağırlıkları (1/√y), χ²/ν ve hata aralıkları ham sayım varsayar; şiddetler ham sayım değilse "
        "(saniye başına sayım, normalize ya da işlenmiş veri) program uyarır.",
        "Cihaz modelinin kalitesi algılama sınırını belirler. İnce adımla (≤ 0,005°) ve Kα2 ayıklanmadan ölçülmüş "
        "bir çizgi standardı, tercihen LaB6 (NIST SRM 660), önerilir.",
        "Aynı veri üzerinde CMWP programıyla doğrudan karşılaştırma henüz yapılmadı."])

    # =================================================================== 16 SOFTWARE
    H(1, "software", "Software and reproducibility", "Yazılım ve yeniden üretilebilirlik")
    P("AutoDisloc is written in Python (NumPy, SciPy [@virtanen2020], pandas, matplotlib) with a PySide6 desktop "
      "interface in Turkish and English, and runs on macOS and Windows. The engine (<code>autodisloc/</code>) can "
      "also be used from the command line or as a library. This document is generated from the engine by "
      "<code>docs/whitepaper/build_whitepaper.py</code>: every number and figure is recomputed when the document is "
      "built. The synthetic examples are reproduced with <code>examples/make_synthetic_example.py</code>.",
      "AutoDisloc, Türkçe ve İngilizce PySide6 masaüstü arayüzüyle Python'da (NumPy, SciPy [@virtanen2020], pandas, "
      "matplotlib) yazılmıştır ve macOS ile Windows'ta çalışır. Hesap motoru (<code>autodisloc/</code>) komut "
      "satırından ya da kütüphane olarak da kullanılabilir. Bu doküman motordan "
      "<code>docs/whitepaper/build_whitepaper.py</code> ile üretilir: doküman her derlendiğinde her sayı ve şekil "
      "yeniden hesaplanır. Sentetik örnekler <code>examples/make_synthetic_example.py</code> ile yeniden üretilir.")
    P("The software is released under the MIT license. If you use it in scientific work, please cite it as given in "
      "<code>CITATION.cff</code> of the repository (Zenodo DOI of the release). Author: Fırat Memu.",
      "Yazılım MIT lisansıyla yayımlanmıştır. Bilimsel çalışmalarda kullanırsanız depodaki <code>CITATION.cff</code> "
      "dosyasındaki künyeyle (sürümün Zenodo DOI'si) kaynak gösterin. Geliştiren: Fırat Memu.")

    return V, B, BIB
