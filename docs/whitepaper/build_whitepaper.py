# SPDX-License-Identifier: MIT
# AutoDisloc 2 - Copyright (c) 2026 Firat Memu
"""Build the AutoDisloc 2 whitepaper (English and Turkish, HTML + PDF).

    python docs/whitepaper/build_whitepaper.py                   # public edition
    AUTODISLOC_PRIVATE_DATA=/folder \
    python docs/whitepaper/build_whitepaper.py --example private # own measured data

Every number and figure is produced by the engine. The public edition uses
the synthetic patterns of examples/ (known microstructure) as the worked
example. The private edition analyses every pattern file of the folder given
in AUTODISLOC_PRIVATE_DATA (sorted by name; the first is the worked example)
and is written to local/whitepaper_private/ (not published).

Typesetting: the text (content.py) is turned into HTML with numbered
sections, equations, figures, tables and citations; equations are rendered
as SVG with matplotlib mathtext (STIX fonts). The PDF is printed with Qt
WebEngine and post-processed with PyMuPDF (page numbers, table-of-contents
page numbers, bookmarks, metadata).
"""

import argparse
import base64
import io
import os
import pickle
import re
import sys
import warnings

warnings.filterwarnings("ignore")
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)

import numpy as np  # noqa: E402

from autodisloc import InstrumentModel, analyze, read_pattern, set_language  # noqa: E402
from autodisloc import figures as F  # noqa: E402
from autodisloc._meta import AUTHOR, VERSION  # noqa: E402
from autodisloc.i18n import get_language, tr  # noqa: E402
from autodisloc.io import Pattern  # noqa: E402
from autodisloc.mwa import ln_fourier  # noqa: E402
from autodisloc.peaks import ka2_position, voigt  # noqa: E402
from autodisloc.pipeline import AnalysisOptions  # noqa: E402
from autodisloc.wholeprofile import fit_whole_profile, rho_profile  # noqa: E402

INST_PATH = os.path.join(ROOT, "autodisloc", "data", "instrument_corundum_example.json")
# own measured data for --example private (not distributed): a folder of pattern files
PRIVATE_DATA = os.environ.get("AUTODISLOC_PRIVATE_DATA", "")
PATTERN_EXT = (".raw", ".uxd", ".xrdml", ".xy", ".dat", ".txt", ".csv")
OUT = {"dir": HERE}


# ---------------------------------------------------------------------------
# computations (language independent, cached)
# ---------------------------------------------------------------------------
def read_truth(path):
    truth = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            m = re.match(r"# true (\S+) = (\S+)", line)
            if m:
                truth[m.group(1)] = float(m.group(2))
    return truth


SYN_CASES = [(3e15, 1.0, (-2.0, -2.5), 60.0, 0.35, 6000.0, 21),
             (5e14, 1.6, (-1.0, -2.0), 120.0, 0.30, 6000.0, 22),
             (1.5e14, 2.0, (-2.5, -1.5), 200.0, 0.25, 6000.0, 23)]


def synthetic_recovery(inst):
    """Fit synthetic patterns of known microstructure."""
    sys.path.insert(0, os.path.join(ROOT, "examples"))
    from make_synthetic_example import synthesize
    rows = []
    for rho, M, u, m, sig, scale, seed in SYN_CASES:
        x, counts, truth = synthesize(rho, M, u, m, sig, scale, seed, inst)
        pat = Pattern(two_theta=x, counts=counts, wl1=1.540598, wl2=1.544426, ka2_ratio=0.5,
                      source="synthetic")
        best = None
        for lr in (14.0, 15.0, 16.0):
            r = fit_whole_profile(pat, inst, start={"log_rho": lr})
            if best is None or r.params["chi2"] < best.params["chi2"]:
                best = r
        rows.append({"rho": rho, "rho_fit": best.rho, "ha": truth["h_a"], "ha_fit": best.h["a"],
                     "M": M, "M_fit": best.M_star, "m": m, "m_fit": best.m_nm,
                     "gof": best.params["chi2"] / best.params["dof"]})
        print("  synthetic", f"{rho:.1e} -> {best.rho:.2e}", flush=True)
    return rows


def compute(example, cache):
    if os.path.exists(cache):
        return pickle.load(open(cache, "rb"))
    inst = InstrumentModel.load(INST_PATH)
    opts = AnalysisOptions(mc_draws=100)
    set_language("en")
    if example == "synthetic":
        ex_dir = os.path.join(ROOT, "examples")
        paths = {"A": os.path.join(ex_dir, "synthetic_Ti64_A.xy"),
                 "B": os.path.join(ex_dir, "synthetic_Ti64_B.xy")}
        results = []
        for n, p in paths.items():
            results.append(analyze(read_pattern(p), inst, n, opts))
            print("  analysed", n, results[-1].summary()["rho_text"], flush=True)
        truth = {n: read_truth(p) for n, p in paths.items()}
    else:
        if not os.path.isdir(PRIVATE_DATA):
            raise SystemExit("--example private: set AUTODISLOC_PRIVATE_DATA to a folder of pattern files")
        files = sorted(f for f in os.listdir(PRIVATE_DATA) if f.lower().endswith(PATTERN_EXT))
        if not files:
            raise SystemExit(f"no pattern files in {PRIVATE_DATA}")
        results = []
        for f in files:
            s = os.path.splitext(f)[0]
            results.append(analyze(read_pattern(os.path.join(PRIVATE_DATA, f)), inst, s, opts))
            print("  analysed", s, results[-1].summary()["rho_text"], flush=True)
        truth = {}
    up = results[-1]
    print("synthetic recovery...", flush=True)
    syn = synthetic_recovery(inst)
    print("profile likelihood...", flush=True)
    fixM = {"log_M": float(np.log10(AnalysisOptions().wp_M_band[0]))}
    ref = fit_whole_profile(up.pattern, inst, start={"log_rho": 14.0}, fix=fixM)
    grid = np.arange(np.floor(8 * np.log10(ref.rho)) / 8, 16.01, 0.125)
    g, chi2 = rho_profile(up.pattern, inst, grid, best=ref, fix=fixM, stop_delta=400)
    g, chi2 = np.r_[np.log10(ref.rho), g], np.r_[ref.params["chi2"], chi2]
    data = {"example": example, "results": results, "truth": truth, "syn": syn,
            "pl": (g, chi2, ref.params["dof"], ref.params["chi2"], up.wp_interval[1])}
    pickle.dump(data, open(cache, "wb"))
    return data


# ---------------------------------------------------------------------------
# whitepaper-only figures
# ---------------------------------------------------------------------------
def T(en, tr_):
    return en if get_language() == "en" else tr_


def fig_pipeline():
    from matplotlib.patches import FancyBboxPatch
    fig = F._fig(F.DOUBLE, 7.4 * F.CM)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 40)
    ax.axis("off")
    boxes = [
        (2, 26, T("Raw pattern\n(.raw / .uxd / .xy)", "Ham desen\n(.raw / .uxd / .xy)"), F.INK2),
        (21, 26, T("Voigt doublets\nKα1 + Kα2", "Voigt ikilileri\nKα1 + Kα2"), F.INK2),
        (40, 26, T("Instrument\ncorrection", "Cihaz\ndüzeltmesi"), F.INK2),
        (59, 26, T("mWH\n(constrained)", "mWH\n(kısıtlı)"), F.INK2),
        (78, 26, T("Burgers-vector\npopulation h, b²C̄", "Burgers vektörü\npopülasyonu h, b²C̄"), F.INK2),
        (40, 6, T("Voigt-mWA\n(comparison)", "Voigt-mWA\n(karşılaştırma)"), F.ORANGE),
        (59, 6, T("Wilkens whole\nprofile: ρ, M*, h, size", "Wilkens tam profil:\nρ, M*, h, boyut"), F.BLUE),
        (78, 6, T("95 % interval\nJacobian / M* band /\nprofile likelihood",
                  "%95 aralık\nJacobian / M* bandı /\nprofil-olabilirlik"), F.BLUE),
    ]
    for x, y, t, c in boxes:
        ax.add_patch(FancyBboxPatch((x, y), 18, 9, boxstyle="round,pad=0.4,rounding_size=1.2",
                                    fc="white", ec=c, lw=1.2))
        ax.text(x + 9, y + 4.5, t, ha="center", va="center", fontsize=7, color=F.INK)
    arr = dict(arrowstyle="-|>", color=F.INK2, lw=0.9)
    for x0, x1 in [(20.5, 21), (39.5, 40), (58.5, 59), (77.5, 78)]:
        ax.annotate("", xy=(x1, 30.5), xytext=(x0, 30.5), arrowprops=arr)
    ax.annotate("", xy=(49, 15.5), xytext=(49, 25.5), arrowprops=arr)
    ax.annotate("", xy=(66, 15.5), xytext=(30, 25.5),
                arrowprops=dict(arrowstyle="-|>", color=F.BLUE, lw=0.9, connectionstyle="arc3,rad=-0.15"))
    ax.annotate("", xy=(70, 15.5), xytext=(86, 25.5),
                arrowprops=dict(arrowstyle="-|>", color=F.BLUE, lw=0.9, connectionstyle="arc3,rad=0.1"))
    ax.annotate("", xy=(77.5, 10.5), xytext=(77, 10.5), arrowprops=arr)
    ax.text(31, 19, T("raw profiles", "ham profiller"), fontsize=6.5, color=F.BLUE, rotation=-14)
    ax.text(80, 19.5, T("start values", "başlangıç"), fontsize=6.5, color=F.BLUE)
    ax.text(2, 9, T("Main result: blue path\nComparison: orange", "Ana sonuç: mavi yol\nKarşılaştırma: turuncu"),
            fontsize=7, color=F.INK2)
    return fig


def fig_peak_decomposition(res):
    pat = res.pattern
    fits = [f for f in res.alpha_fits if f.label in ("00.2", "10.1")]
    a, b = min(f.center for f in fits) - 1.0, max(f.center for f in fits) + 1.0
    m = (pat.two_theta > a) & (pat.two_theta < b)
    x, y = pat.two_theta[m], pat.counts[m]
    fig = F._fig(F.DOUBLE, 6.3 * F.CM)
    ax = fig.add_subplot()
    ax.plot(x, y, "o", ms=2, mfc="none", mec=F.INK2, mew=0.5, label=tr("fig.measured"))
    xs = np.linspace(a, b, 1500)
    total = np.zeros_like(xs)
    for f in fits:
        k1 = voigt(xs, f.center, f.area, f.wg, f.wl)
        k2 = pat.ka2_ratio * voigt(xs, ka2_position(f.center, pat.wl1, pat.wl2), f.area, f.wg, f.wl)
        ax.fill_between(xs, 0, k1, color=F.BLUE, alpha=0.25, lw=0,
                        label=T("Kα1 component", "Kα1 bileşeni") if f.label == "00.2" else None)
        ax.fill_between(xs, 0, k2, color=F.ORANGE, alpha=0.35, lw=0,
                        label=T("Kα2 component (I₂/I₁ = 0.5)", "Kα2 bileşeni (I₂/I₁ = 0.5)")
                        if f.label == "00.2" else None)
        total += k1 + k2
        ax.annotate(f.label, (f.center, (k1 + k2).max()), xytext=(4, 4), textcoords="offset points", fontsize=7)
    bg = np.percentile(y, 5)
    ax.plot(xs, total + bg, color=F.INK, lw=1.0, label=T("Total model + background", "Toplam model + zemin"))
    ax.set_xlabel("2θ (°)")
    ax.set_ylabel(tr("fig.counts"))
    ax.legend(loc="upper left")
    F._style(ax)
    return fig


def fig_voigt_ft(res):
    """Fourier coefficients of the broadest Voigt profile: numerical cosine
    transform, correct closed form and the erroneous form."""
    from scipy.special import voigt_profile
    t = res.peaks
    i = int(np.argmax(t["wL_t"].values + t["wG_t"].values))
    wg, wl = float(t["wG_t"].values[i]), float(t["wL_t"].values[i])
    K = np.linspace(-4, 4, 2 ** 19)
    dK = K[1] - K[0]
    I = voigt_profile(K, max(wg, 1e-6) / (2 * np.sqrt(2 * np.log(2))), max(wl, 1e-6) / 2)
    I /= I.sum() * dK
    L = np.linspace(0, 120, 61)
    num = np.array([(I * np.cos(2 * np.pi * l * K)).sum() * dK for l in L])
    fig = F._fig(F.SINGLE * 1.25, 6.2 * F.CM)
    ax = fig.add_subplot()
    ax.plot(L, num, "o", ms=3.5, mfc="none", mec=F.INK2, mew=0.7,
            label=T("numerical cosine transform", "sayısal kosinüs dönüşümü"))
    ax.plot(L, np.exp(ln_fourier(L, [wg], [wl], "voigt")[:, 0]), color=F.BLUE,
            label=T("closed form, this work", "kapalı biçim, bu çalışma"))
    ax.plot(L, np.exp(ln_fourier(L, [wg], [wl], "eq13")[:, 0]), color=F.ORANGE, ls="--",
            label=r"$\exp(-L^2w_G^2/2-Lw_L)$")
    ax.set_xlabel(tr("fig.L_axis"))
    ax.set_ylabel("A(L)")
    ax.set_ylim(0, 1.02)
    ax.set_xlim(0, L.max())
    ax.legend(loc="upper right")
    ax.set_title(f"{t['hkl'].values[i]}: $w_G$ = {wg * 1e3:.1f}, $w_L$ = {wl * 1e3:.1f} "
                 f"($10^{{-3}}$ nm$^{{-1}}$)", loc="left")
    F._style(ax)
    return fig


def fig_synthetic(rows):
    fig = F._fig(F.SINGLE, 6.2 * F.CM)
    ax = fig.add_subplot()
    t = np.array([r["rho"] for r in rows])
    f = np.array([r["rho_fit"] for r in rows])
    lim = [t.min() / 3, t.max() * 3]
    ax.plot(lim, lim, color=F.MUTED, lw=0.8, ls="--", label="y = x")
    ax.plot(t, f, "o", ms=7, mfc=F.BLUE, mec="white", mew=0.8,
            label=T("whole-profile fit", "tam profil uydurması"))
    for a, b in zip(t, f):
        ax.annotate(f"{100 * (b / a - 1):+.0f} %", (a, b), xytext=(6, -3), textcoords="offset points", fontsize=7)
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlim(lim)
    ax.set_ylim(lim)
    ax.set_xlabel(T("true ρ (m$^{-2}$)", "gerçek ρ (m$^{-2}$)"))
    ax.set_ylabel(T("fitted ρ (m$^{-2}$)", "bulunan ρ (m$^{-2}$)"))
    ax.legend(loc="upper left")
    F._style(ax)
    return fig


def fig_profile_likelihood(pl):
    g, chi2, dof, chi2_ref, upper = pl
    fig = F._fig(F.SINGLE, 6.0 * F.CM)
    ax = fig.add_subplot()
    c0 = min(chi2_ref, np.nanmin(chi2))
    ok = np.isfinite(chi2)
    ax.plot(10 ** g[ok], (chi2[ok] - c0) / (c0 / dof), "o-", ms=3.5, color=F.BLUE, mfc=F.BLUE, mec="white")
    ax.axhline(3.84, color=F.ORANGE, lw=1.0, ls="--",
               label=T("95 % threshold (Δχ² = 3.84)", "%95 eşiği (Δχ² = 3.84)"))
    if upper and np.isfinite(upper):
        ax.axvline(upper, color=F.INK2, lw=0.8)
        ax.annotate(T("upper limit", "üst sınır") + f"\n{upper:.1e} m$^{{-2}}$", (upper, 3.84),
                    xytext=(6, 12), textcoords="offset points", fontsize=7)
    ax.set_xscale("log")
    ax.set_yscale("symlog", linthresh=1)
    ax.set_xlabel(T("fixed ρ (m$^{-2}$)", "sabitlenen ρ (m$^{-2}$)"))
    ax.set_ylabel(T("Δχ² (scaled)", "Δχ² (ölçeklenmiş)"))
    ax.legend(loc="upper left")
    F._style(ax)
    return fig


def make_figures(data, inst, figdir):
    os.makedirs(figdir, exist_ok=True)
    res = data["results"]
    ex = res[0]

    def save(fig, name):
        path = os.path.join(figdir, name + ".png")
        F.save_figure(fig, path, dpi=300)
        return os.path.relpath(path, OUT["dir"]).replace(os.sep, "/")

    return {
        "pipeline": save(fig_pipeline(), "f_pipeline"),
        "pattern": save(F.fig_pattern(ex), "f_pattern"),
        "peak": save(fig_peak_decomposition(ex), "f_doublet"),
        "inst": save(F.fig_instrument(inst), "f_instrument"),
        "wilkens": save(F.fig_wilkens(), "f_wilkens"),
        "burgers": save(F.fig_burgers(ex), "f_burgers"),
        "mwh": save(F.fig_mwh(ex), "f_mwh"),
        "voigtft": save(fig_voigt_ft(ex), "f_voigt_ft"),
        "mwa": save(F.fig_mwa(ex), "f_mwa"),
        "fourier": save(F.fig_fourier_components(ex), "f_fourier"),
        "wp": save(F.fig_wholeprofile(ex), "f_whole_profile"),
        "pl": save(fig_profile_likelihood(data["pl"]), "f_profile_likelihood"),
        "syn": save(fig_synthetic(data["syn"]), "f_synthetic"),
        "compare": save(F.fig_compare(res), "f_compare"),
    }


# ---------------------------------------------------------------------------
# typesetting
# ---------------------------------------------------------------------------
def _mathtext(tex, display=False):
    """LaTeX subset -> matplotlib mathtext (display equations get \\dfrac)."""
    rep = [(r"\text{", r"\mathrm{"), (r"\tfrac", r"\frac"), (r"\dfrac", r"\frac"), (r"\lt", "<"),
           (r"\gt", ">"), (r"\!", ""), (r"\displaystyle", "")]
    for a, b in rep:
        tex = tex.replace(a, b)
    if display:
        tex = tex.replace(r"\frac", r"\dfrac")
    tex = re.sub(r"\\(qquad|quad)", r"\\quad", tex)
    tex = re.sub(r"\\ge(?![a-z])", r"\\geq", tex)
    tex = re.sub(r"\\le(?![a-z])", r"\\leq", tex)
    tex = tex.replace("\\ ", "\\;").replace("\n", " ")
    return tex


_math_cache = {}


def math_img(tex, display):
    key = (tex, display)
    if key in _math_cache:
        return _math_cache[key]
    from matplotlib import mathtext
    from matplotlib.font_manager import FontProperties
    import matplotlib as mpl
    buf = io.BytesIO()
    with mpl.rc_context({"mathtext.fontset": "stix", "mathtext.default": "it"}):
        prop = FontProperties(size=14.0 if display else 12.0, math_fontfamily="stix")
        try:
            mathtext.math_to_image("$" + _mathtext(tex, display) + "$", buf, prop=prop, format="svg")
        except Exception as e:
            raise ValueError(f"mathtext cannot render: {tex}") from e
    svg = buf.getvalue()
    b64 = base64.b64encode(svg).decode()
    m = re.search(rb'width="([0-9.]+)pt" height="([0-9.]+)pt"', svg)
    w, h = (float(m.group(1)), float(m.group(2))) if m else (0, 0)
    style = f"width:{w * 1.333:.1f}px;height:{h * 1.333:.1f}px"
    cls = "dm" if display else "im"
    out = f'<img class="{cls}" style="{style}" src="data:image/svg+xml;base64,{b64}">'
    _math_cache[key] = out
    return out


class Doc:
    """Numbering of sections, equations, figures, tables and citations.

    Blocks (lists) produced by content.py:
      ["h", level, label, text, numbered]   ["p", text]   ["note", text, css]
      ["ul", items, ordered]                ["eq", label, tex]
      ["fig", label, src, caption, width]   ["tab", label, caption, head, rows, css]
    Inline markup: $math$, [@key; @key2] citations, @eq:/@fig:/@tab:/@sec:label
    references, «name» value placeholders.
    """

    def __init__(self, blocks, bib, lang):
        self.blocks, self.bib, self.lang = blocks, bib, lang
        self.labels, self.cites, self.toc = {}, {}, []
        sec = [0, 0, 0]
        n = {"eq": 0, "fig": 0, "tab": 0}
        for idx, b in enumerate(blocks):
            kind = b[0]
            if kind == "h":
                _, level, label, text, numbered = b[:5]
                num = ""
                if numbered:
                    sec[level - 1] += 1
                    for k in range(level, 3):
                        sec[k] = 0
                    num = ".".join(str(v) for v in sec[:level])
                anchor = label or f"h{idx}"
                b += [num, anchor]
                if label:
                    self.labels[("sec", label)] = num
                if level <= 2:
                    self.toc.append((level, num, text, anchor))
            elif kind in ("eq", "fig", "tab"):
                n[kind] += 1
                b.append(n[kind])
                if b[1]:
                    if (kind, b[1]) in self.labels:
                        raise KeyError("duplicate label " + b[1])
                    self.labels[(kind, b[1])] = str(n[kind])
        for b in blocks:
            for s in self._texts(b):
                for grp in re.findall(r"\[@([^\]]+)\]", s):
                    for key in self._keys(grp):
                        if key not in bib:
                            raise KeyError(f"unknown citation {key}")
                        if key not in self.cites:
                            self.cites[key] = len(self.cites) + 1

    @staticmethod
    def _keys(grp):
        return [k.strip().lstrip("@").strip() for k in grp.split(";")]

    @staticmethod
    def _texts(b):
        kind = b[0]
        if kind == "code":
            return []
        if kind in ("p", "note"):
            return [b[1]]
        if kind == "fig":
            return [b[3]]
        if kind == "tab":
            return [b[2]] + [str(c) for row in b[4] for c in row] + list(b[3])
        if kind == "ul":
            return list(b[1])
        if kind == "h":
            return [b[3]]
        return []

    def inline(self, s, values):
        for k, v in values.items():
            s = s.replace(f"«{k}»", str(v))
        if "«" in s:
            raise KeyError("unreplaced placeholder in: " + s[:120])
        maths = []

        def keep(m):
            maths.append(m.group(1))
            return f"\x00{len(maths) - 1}\x00"

        s = re.sub(r"\$(.+?)\$", keep, s, flags=re.S)

        def cite(m):
            nums = sorted(self.cites[k] for k in self._keys(m.group(1)))
            parts, i = [], 0
            while i < len(nums):
                j = i
                while j + 1 < len(nums) and nums[j + 1] == nums[j] + 1:
                    j += 1
                parts.append(f"{nums[i]}–{nums[j]}" if j - i >= 2 else ", ".join(map(str, nums[i:j + 1])))
                i = j + 1
            return f'<a class="cite" href="#bib">[{", ".join(parts)}]</a>'

        s = re.sub(r"\[@([^\]]+)\]", cite, s)

        s = re.sub(REF_GROUP, lambda m: self._ref_group(m), s)
        s = re.sub(r"\x00(\d+)\x00", lambda m: math_img(maths[int(m.group(1))], False), s)
        return s

    def _ref_group(self, m):
        """A run of references of one kind, e.g. '@eq:a–@eq:b' or '@sec:x, @sec:y and @sec:z',
        optionally followed by a Turkish case suffix ('deki, 'yi, ...)."""
        kind = m.group(1)
        body, suffix = m.group(0), m.group("suf")
        if suffix:
            body = body[: -len(suffix) - 1]
        parts = re.split(r"(@(?:eq|fig|tab|sec):[A-Za-z0-9_\-]*[A-Za-z0-9])", body)
        out, nums = [], []
        for part in parts:
            if part.startswith("@"):
                k, label = part[1:].split(":", 1)
                if (k, label) not in self.labels:
                    raise KeyError(f"unknown label {k}:{label}")
                n = self.labels[(k, label)]
                nums.append(n)
                txt = f"({n})" if k == "eq" else n
                out.append(f'<a href="#{k}-{label}">{txt}</a>')
            else:
                out.append(part)
        en = self.lang == "en"
        many = len(nums) > 1
        word = {"eq": ("Eqs." if many else "Eq.") if en else "Denk.",
                "fig": ("Figs." if many else "Fig.") if en else "Şekil",
                "tab": ("Tables" if many else "Table") if en else "Tablo",
                "sec": ("Sections" if many else "Section") if en else "Bölüm"}[kind]
        txt = word + "&nbsp;" + "".join(out)
        if suffix:
            txt += "'" + tr_suffix(nums[-1], suffix)
        return txt

    def render(self, values):
        L = self.lang == "en"
        out = []
        for b in self.blocks:
            kind = b[0]
            if kind == "h":
                level, text, num, anchor = b[1], b[3], b[5], b[6]
                tag = f"h{level + 1}"
                out.append(f'<{tag} id="sec-{anchor}">{(num + "&ensp;") if num else ""}'
                           f'{self.inline(text, values)}</{tag}>')
            elif kind == "p":
                out.append(f"<p>{self.inline(b[1], values)}</p>")
            elif kind == "note":
                out.append(f'<div class="{b[2]}">{self.inline(b[1], values)}</div>')
            elif kind == "ul":
                tag = "ol" if b[2] else "ul"
                out.append(f"<{tag}>" + "".join(f"<li>{self.inline(i, values)}</li>" for i in b[1]) + f"</{tag}>")
            elif kind == "eq":
                _, label, tex, num = b
                out.append(f'<div class="eq" id="eq-{label}"><span class="eqm">{math_img(tex, True)}</span>'
                           f'<span class="eqn">({num})</span></div>')
            elif kind == "fig":
                _, label, src, cap, width, num = b
                word = "Figure" if L else "Şekil"
                out.append(f'<figure id="fig-{label}" style="--w:{width}"><img src="{src}">'
                           f'<figcaption><b>{word} {num}.</b> {self.inline(cap, values)}</figcaption></figure>')
            elif kind == "tab":
                _, label, cap, head, rows, css, num = b
                word = "Table" if L else "Tablo"
                h = "".join(f"<th>{self.inline(c, values)}</th>" for c in head)
                r = "".join("<tr>" + "".join(f"<td>{self.inline(str(c), values)}</td>" for c in row) + "</tr>"
                            for row in rows)
                out.append(f'<div class="tab {css}" id="tab-{label}"><div class="tcap"><b>{word} {num}.</b> '
                           f'{self.inline(cap, values)}</div><table><tr>{h}</tr>{r}</table></div>')
            elif kind == "code":
                import html as _h
                out.append(f'<pre class="code">{_h.escape(b[1])}</pre>')
            elif kind == "img":
                out.append(f'<div class="inlineimg"><img src="{b[1]}" style="width:{b[2]}"></div>')
            elif kind == "pagebreak":
                out.append('<div class="pagebreak"></div>')
        bib = "".join(f'<li value="{n}">{self.bib[k]}</li>'
                      for k, n in sorted(self.cites.items(), key=lambda kv: kv[1]))
        out.append(f'<h2 id="bib">{"References" if L else "Kaynaklar"}</h2><ol class="bib">{bib}</ol>')
        return "\n".join(out)

    def toc_html(self, pages, refs=True):
        rows = []
        for i, (level, num, text, anchor) in enumerate(self.toc):
            pg = pages.get(i, "") if pages is not None else "00"
            rows.append(f'<div class="toc{level}"><span class="tn">{num}</span>'
                        f'<span class="tt"><a href="#sec-{anchor}">{self.inline(text, {})}</a></span>'
                        f'<span class="tp">{pg}</span></div>')
        if not refs:
            return "".join(rows)
        pg = pages.get("bib", "") if pages is not None else "00"
        rows.append(f'<div class="toc1"><span class="tn"></span><span class="tt"><a href="#bib">'
                    f'{"References" if self.lang == "en" else "Kaynaklar"}</a></span><span class="tp">{pg}</span></div>')
        return "".join(rows)


_REF = r"@(?:eq|fig|tab|sec):[A-Za-z0-9_\-]*[A-Za-z0-9]"
REF_GROUP = (r"@(eq|fig|tab|sec):[A-Za-z0-9_\-]*[A-Za-z0-9]"
             r"(?:(?:\s*,\s*|\s*–\s*|\s+and\s+|\s+ve\s+)@\1:[A-Za-z0-9_\-]*[A-Za-z0-9])*"
             r"(?:'(?P<suf>[a-zçğıöşü]+))?")

_ONES = {0: "sıfır", 1: "bir", 2: "iki", 3: "üç", 4: "dört", 5: "beş", 6: "altı", 7: "yedi", 8: "sekiz", 9: "dokuz"}
_TENS = {1: "on", 2: "yirmi", 3: "otuz", 4: "kırk", 5: "elli", 6: "altmış", 7: "yetmiş", 8: "seksen", 9: "doksan"}


def _tr_word(numstr):
    """Turkish reading of the last number of '10.3' / '13' (the word the suffix attaches to)."""
    n = int(re.findall(r"\d+", numstr)[-1])
    if n % 10:
        return _ONES[n % 10]
    if n == 0:
        return _ONES[0]
    if n % 100 == 0:
        return "yüz"
    return _TENS[(n // 10) % 10]


def tr_suffix(numstr, suffix):
    """Re-inflect a Turkish case suffix for the number it follows (vowel harmony,
    consonant assimilation, buffer consonants)."""
    w = _tr_word(numstr)
    vowels = [c for c in w if c in "aeıioöuü"]
    v = vowels[-1]
    back = v in "aıou"
    v2 = "a" if back else "e"
    v4 = {"a": "ı", "ı": "ı", "o": "u", "u": "u", "e": "i", "i": "i", "ö": "ü", "ü": "ü"}[v]
    ends_vowel = w[-1] in "aeıioöuü"
    d = "t" if w[-1] in "fstkçşhp" else "d"
    tail = ""
    base = suffix
    for extra in ("yle", "yla"):
        if base.endswith(extra) and len(base) > 3:
            base, tail = base[:-3], "y" + "l" + v2
    if base in ("i", "ı", "u", "ü", "yi", "yı", "yu", "yü"):
        out = ("y" if ends_vowel else "") + v4
    elif base in ("in", "ın", "un", "ün", "nin", "nın", "nun", "nün"):
        out = ("n" if ends_vowel else "") + v4 + "n"
    elif base in ("e", "a", "ye", "ya"):
        out = ("y" if ends_vowel else "") + v2
    elif base in ("de", "da", "te", "ta"):
        out = d + v2
    elif base in ("den", "dan", "ten", "tan"):
        out = d + v2 + "n"
    elif base in ("deki", "daki", "teki", "taki"):
        out = d + v2 + "ki"
    elif base in ("dir", "dır", "dur", "dür", "tir", "tır", "tur", "tür"):
        out = d + v4 + "r"
    else:
        return suffix
    return out + tail


CSS = r"""
:root { --ink:#1d1d1b; --ink2:#52514e; --muted:#8a8984; --rule:#d9d8d2; --accent:#2a78d6; }
html { background: #ffffff; }
body { font-family: "Charter", "Georgia", "Times New Roman", serif; color: var(--ink); background: #ffffff;
       max-width: 760px; margin: 0 auto; line-height: 1.5; font-size: 10.6pt; text-align: justify; hyphens: auto; }
h1, h2, h3, h4, figcaption, .tcap, table, .toc1, .toc2, .meta, .kw { font-family: -apple-system, "Helvetica Neue", "Segoe UI", Arial, sans-serif; }
h1 { font-size: 21pt; line-height: 1.18; margin: 0 0 8px; text-align: left; letter-spacing: -0.01em; }
h2 { font-size: 13.5pt; margin: 20px 0 6px; padding-top: 6px; border-top: 1px solid var(--rule); text-align: left; page-break-after: avoid; }
h3 { font-size: 11.4pt; margin: 13px 0 4px; text-align: left; page-break-after: avoid; }
h4 { font-size: 10.6pt; margin: 10px 0 3px; text-align: left; page-break-after: avoid; }
.pagebreak { page-break-before: always; height: 0; }
p { margin: 0 0 7px; orphans: 3; widows: 3; }
a { color: inherit; text-decoration: none; }
a.cite, a[href^="#eq-"], a[href^="#fig-"], a[href^="#tab-"], p a[href^="#sec-"], li a[href^="#sec-"] { color: #1f5fae; }
.meta { color: var(--ink2); font-size: 10pt; line-height: 1.5; margin-bottom: 12px; text-align: left; }
.abstract { border-left: 3px solid var(--accent); background: #f5f8fd; padding: 9px 13px; margin: 12px 0 6px; font-size: 10.1pt; }
.kw { font-size: 9.2pt; color: var(--ink2); margin: 4px 0 12px; text-align: left; }
figure { margin: 10px auto 14px; page-break-inside: avoid; width: calc(var(--w) * 100%); }
figure img { width: 100%; height: auto; display: block; }
figcaption { font-size: 8.9pt; color: var(--ink2); margin-top: 5px; text-align: left; line-height: 1.4; }
figcaption b, .tcap b { color: var(--ink); }
.tab { margin: 10px 0 14px; page-break-inside: avoid; }
.tcap { font-size: 8.9pt; color: var(--ink2); margin-bottom: 4px; text-align: left; line-height: 1.4; }
table { border-collapse: collapse; width: 100%; font-size: 8.6pt; text-align: left; }
th, td { border-bottom: 0.6px solid var(--rule); padding: 3px 5px; vertical-align: top; }
th { border-top: 1.2px solid var(--ink2); border-bottom: 0.9px solid var(--ink2); font-weight: 600; }
tr:last-child td { border-bottom: 1.2px solid var(--ink2); }
.eq { display: flex; align-items: center; margin: 7px 0 9px; page-break-inside: avoid; }
.eqm { flex: 1; text-align: center; }
.eqn { width: 44px; text-align: right; font-size: 10.4pt; }
img.dm { max-width: 100%; vertical-align: middle; }
img.im { display: inline; vertical-align: middle; margin: 0 1px; position: relative; top: -1px; }
.note { font-size: 9.6pt; background: #faf9f6; border: 1px solid var(--rule); border-radius: 4px; padding: 7px 11px; margin: 8px 0; }
.warn { font-size: 9.6pt; border-left: 3px solid #eb6834; background: #fdf5f1; padding: 7px 11px; margin: 8px 0; }
.example { font-size: 9.8pt; border-left: 3px solid #1baf7a; background: #f2faf6; padding: 7px 11px; margin: 8px 0; page-break-inside: avoid; }
.example b.lbl { font-family: -apple-system, "Helvetica Neue", Arial, sans-serif; color: #127a55; }
ul, ol { margin: 3px 0 8px; padding-left: 22px; }
li { margin-bottom: 2px; }
ol.bib { font-size: 9pt; padding-left: 28px; text-align: left; }
ol.bib li { margin-bottom: 3px; }
.toc1, .toc2 { display: flex; line-height: 1.55; }
.toc1 { font-weight: 600; font-size: 9.8pt; margin-top: 2px; }
.toc2 { font-size: 9.3pt; }
.toc1 .tn { width: 30px; flex: none; } .toc2 .tn { width: 30px; flex: none; padding-left: 30px; }
.tt { flex: 1; }
.tp { width: 30px; text-align: right; }
code { font-family: "SF Mono", Menlo, Consolas, monospace; font-size: 8.6pt; background: #f3f2ee; padding: 0 3px; border-radius: 2px; }
.sym td:first-child { width: 17%; } .sym td:last-child { width: 14%; } .abbr td:first-child { width: 14%; } .gloss td:first-child { width: 24%; }
@media screen { body { padding: 28px 22px 60px; } }
"""


def front_matter(doc, values, lang, pages):
    L = lang == "en"
    title = ("AutoDisloc 2: Dislocation Density of hcp Ti&#8209;6Al&#8209;4V from X-ray Line Profile Analysis"
             if L else "AutoDisloc 2: X-Işını Çizgi Profili Analiziyle hcp Ti&#8209;6Al&#8209;4V'de Dislokasyon Yoğunluğu")
    sub = ("Mathematical background, implementation and validation — technical whitepaper"
           if L else "Matematiksel temel, uygulama ve doğrulama — teknik doküman (whitepaper)")
    meta = (f"<b>{AUTHOR}</b><br>{'Software version' if L else 'Yazılım sürümü'} {VERSION} · "
            f"{'November 2026' if L else 'Kasım 2026'} · {'License' if L else 'Lisans'}: MIT")
    abstract = doc.inline(values["abstract"], values)
    kw = doc.inline(values["keywords"], values)
    head = "Abstract" if L else "Özet"
    return (f'<h1>{title}</h1><div class="meta">{sub}<br>{meta}</div>'
            f'<div class="abstract"><b>{head}.</b> {abstract}</div><div class="kw">{kw}</div>'
            f'<h2 id="toc">{"Contents" if L else "İçindekiler"}</h2>{doc.toc_html(pages)}'
            '<div class="pagebreak"></div>')


def html_page(body, lang):
    return (f'<!doctype html><html lang="{lang}"><head><meta charset="utf-8">'
            f'<meta name="author" content="{AUTHOR}"><meta name="generator" content="AutoDisloc {VERSION}">'
            f'<title>AutoDisloc 2 Whitepaper</title><style>{CSS}</style></head><body>{body}</body></html>')


def to_pdf(html_path, pdf_path):
    from PySide6.QtCore import QMarginsF, QTimer, QUrl
    from PySide6.QtGui import QPageLayout, QPageSize
    from PySide6.QtWebEngineCore import QWebEnginePage
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance() or QApplication(sys.argv)
    page = QWebEnginePage()
    page.pdfPrintingFinished.connect(lambda path, ok: app.quit())

    def go(ok):
        layout = QPageLayout(QPageSize(QPageSize.A4), QPageLayout.Portrait,
                             QMarginsF(19, 17, 19, 20), QPageLayout.Millimeter)
        QTimer.singleShot(700, lambda: page.printToPdf(pdf_path, layout))

    page.loadFinished.connect(go)
    page.load(QUrl.fromLocalFile(html_path))
    app.exec()


def find_pages(pdf_path, doc, toc_title=None):
    """Page (1-based) of every table-of-contents heading. The search starts
    after the contents: after the first page by default, or, with
    ``toc_title``, after the page that carries this title and any following
    pages that are continuations of the contents (many headings listed)."""
    import fitz
    d = fitz.open(pdf_path)
    texts = [" ".join(p.get_text().split()) for p in d]
    needles = []
    for level, num, text, anchor in doc.toc:
        plain = re.sub(r"<[^>]+>", "", re.sub(r"\$.*?\$", "", text))
        needles.append(" ".join(f"{num} {plain}".split())[:36])
    pages = {}
    start = 1          # skip the contents page itself
    if toc_title:
        first = next((k for k, t in enumerate(texts) if t.startswith(toc_title) or f" {toc_title} " in t[:400]), 0)
        start = first + 1
        while start < len(texts) and sum(n in texts[start] for n in needles) >= 8:
            start += 1
    for i, needle in enumerate(needles):
        for k in range(start, len(texts)):
            if needle in texts[k]:
                pages[i] = k + 1
                start = k
                break
    refs = "References" if doc.lang == "en" else "Kaynaklar"
    for k in range(len(texts) - 1, 0, -1):
        if refs in texts[k]:
            pages["bib"] = k + 1
            break
    return pages


def finish_pdf(pdf_path, doc, pages, lang, short=None, title="AutoDisloc 2 Whitepaper"):
    import fitz
    d = fitz.open(pdf_path)
    n = len(d)
    short = short or ("AutoDisloc 2 — whitepaper" if lang == "en" else "AutoDisloc 2 — teknik doküman")
    grey = (0.45, 0.45, 0.43)
    # a TrueType font with Turkish glyphs (the base-14 Helvetica lacks e.g. "ı")
    ff = next((f for f in ("/System/Library/Fonts/Supplemental/Arial.ttf", "C:/Windows/Fonts/arial.ttf",
                           "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf") if os.path.exists(f)), None)
    font = fitz.Font(fontfile=ff) if ff else fitz.Font("helv")
    kw = {"fontname": "F0", "fontfile": ff} if ff else {"fontname": "helv"}
    for i, p in enumerate(d):
        r = p.rect
        y = r.height - 26
        p.insert_text((54, y), f"{short} · F. Memu", fontsize=7.5, color=grey, **kw)
        s = f"{i + 1} / {n}"
        p.insert_text((r.width - 54 - font.text_length(s, 7.5), y), s, fontsize=7.5, color=grey, **kw)
    toc = [[level, re.sub(r"<[^>]+>|\$", "", f"{num} {text}".strip()), pages[i]]
           for i, (level, num, text, anchor) in enumerate(doc.toc) if i in pages]
    if "bib" in pages:
        toc.append([1, "References" if lang == "en" else "Kaynaklar", pages["bib"]])
    d.set_toc(toc)
    d.set_metadata({"title": title, "author": AUTHOR,
                    "subject": "Dislocation density of hcp Ti-6Al-4V from X-ray line profile analysis",
                    "keywords": "XRD; line profile analysis; dislocation density; mWH; mWA; Wilkens",
                    "creator": f"AutoDisloc {VERSION}", "producer": "Qt WebEngine + PyMuPDF"})
    tmp = pdf_path + ".tmp"
    d.save(tmp, garbage=3, deflate=True)
    d.close()
    os.replace(tmp, pdf_path)


def write_html(path, doc, values, lang, pages):
    body = front_matter(doc, values, lang, pages) + doc.render(values)
    with open(path, "w", encoding="utf-8") as f:
        f.write(html_page(body, lang))


# ---------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--example", choices=["synthetic", "private"], default="synthetic")
    ap.add_argument("--lang", choices=["en", "tr", "both"], default="both")
    ap.add_argument("--no-pdf", action="store_true")
    ap.add_argument("--recompute", action="store_true")
    args = ap.parse_args()
    out_dir = HERE if args.example == "synthetic" else os.path.join(ROOT, "local", "whitepaper_private")
    os.makedirs(out_dir, exist_ok=True)
    OUT["dir"] = out_dir
    cache = os.path.join(out_dir, f"_cache_{args.example}.pkl")
    if args.recompute and os.path.exists(cache):
        os.remove(cache)
    data = compute(args.example, cache)
    inst = InstrumentModel.load(INST_PATH)
    import content
    for lang in (["en", "tr"] if args.lang == "both" else [args.lang]):
        set_language(lang)
        print(f"[{lang}] figures...", flush=True)
        figs = make_figures(data, inst, os.path.join(out_dir, f"figs_{lang}"))
        values, blocks, bib = content.build(lang, data, figs, inst)
        doc = Doc(blocks, bib, lang)
        base = os.path.join(out_dir, f"AutoDisloc2_Whitepaper_{lang.upper()}")
        write_html(base + ".html", doc, values, lang, None)
        print(f"[{lang}] html:", base + ".html", flush=True)
        if args.no_pdf:
            continue
        to_pdf(base + ".html", base + ".pdf")
        pages = find_pages(base + ".pdf", doc)
        for _ in range(2):
            write_html(base + ".html", doc, values, lang, pages)
            to_pdf(base + ".html", base + ".pdf")
            new = find_pages(base + ".pdf", doc)
            if new == pages:
                break
            pages = new
        finish_pdf(base + ".pdf", doc, pages, lang)
        missing = [t[2] for i, t in enumerate(doc.toc) if i not in pages]
        print(f"[{lang}] pdf:", base + ".pdf", "| toc entries without page:", missing, flush=True)


if __name__ == "__main__":
    main()
