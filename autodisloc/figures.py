# SPDX-License-Identifier: MIT
# AutoDisloc 2 - Copyright (c) 2026 Firat Memu
"""Publication-quality figures of an analysis (matplotlib, no pyplot state).

Every function returns a matplotlib Figure sized for a journal column
(single 8.5 cm, double 17.5 cm). ``save_figure`` writes PNG/TIFF at 600 dpi
and vector PDF/SVG. The colours are the first three slots of a CVD-validated
categorical palette; text stays black/grey, identity is never colour alone.
"""

import numpy as np
from matplotlib.figure import Figure
from matplotlib.patches import Polygon
from scipy.spatial import ConvexHull

from ._meta import software
from .contrast import BURGERS_NM, TI_SUBSYSTEMS, type_parabolas
from .i18n import tr
from .mwa import ETA_FACTOR
from .peaks import voigt, ka2_position

CM = 1 / 2.54
SINGLE = 8.5 * CM
DOUBLE = 17.5 * CM

BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"
INK, INK2, MUTED, GRID = "#0b0b0b", "#52514e", "#8a8984", "#e4e3df"
TYPE_COLOR = {"a": BLUE, "c": ORANGE, "c+a": AQUA}
TYPE_LABEL = {"a": "<a>", "c": "<c>", "c+a": "<c+a>"}

RC = {
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
    "font.size": 8,
    "axes.labelsize": 8,
    "axes.titlesize": 8.5,
    "axes.linewidth": 0.7,
    "axes.edgecolor": INK2,
    "axes.labelcolor": INK,
    "xtick.labelsize": 7,
    "ytick.labelsize": 7,
    "xtick.color": INK2,
    "ytick.color": INK2,
    "xtick.direction": "in",
    "ytick.direction": "in",
    "xtick.major.width": 0.6,
    "ytick.major.width": 0.6,
    "legend.fontsize": 7,
    "legend.frameon": False,
    "lines.linewidth": 1.2,
    "savefig.bbox": "tight",
    "savefig.pad_inches": 0.03,
    "mathtext.default": "regular",
}


def apply_style():
    """Journal style for every figure of the program."""
    import matplotlib as mpl
    mpl.rcParams.update(RC)


apply_style()


def _fig(w, h):
    return Figure(figsize=(w, h), dpi=150, layout="constrained")


def _style(ax):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.tick_params(which="both", direction="in", length=3, width=0.6, labelsize=7,
                   colors=INK2)
    ax.xaxis.label.set_size(8)
    ax.yaxis.label.set_size(8)
    ax.title.set_size(8.5)
    for t in ax.get_xticklabels() + ax.get_yticklabels():
        t.set_fontsize(7)


def _panel(ax, letter):
    ax.text(-0.02, 1.02, f"({letter})", transform=ax.transAxes, ha="right", va="bottom",
            fontsize=9, fontweight="bold", color=INK)


def save_figure(fig, path, dpi=600):
    """Save by extension (.png, .tif, .pdf, .svg). The file metadata record
    only the program name and version as software/creator."""
    import matplotlib as mpl
    with mpl.rc_context(RC):
        low = path.lower()
        kw = {"dpi": dpi} if low.endswith((".png", ".tif", ".tiff", ".jpg")) else {}
        soft = software()
        if low.endswith((".tif", ".tiff")):
            # 305 Software (ASCII tag)
            kw["pil_kwargs"] = {"compression": "tiff_lzw", "tiffinfo": {305: soft}}
        elif low.endswith(".png"):
            kw["metadata"] = {"Software": soft}
        elif low.endswith(".pdf"):
            kw["metadata"] = {"Creator": soft}
        elif low.endswith(".svg"):
            kw["metadata"] = {"Creator": soft}
        fig.savefig(path, facecolor="white", **kw)


# ---------------------------------------------------------------------------
def fig_pattern(res, log=True):
    """Measured pattern with reflection markers and the fitted model."""
    pat = res.pattern
    fig = _fig(DOUBLE, 7.5 * CM)
    gs = fig.add_gridspec(2, 1, height_ratios=[4, 1])
    ax = fig.add_subplot(gs[0])
    axr = fig.add_subplot(gs[1], sharex=ax)
    x, y = pat.two_theta, pat.counts
    ax.plot(x, np.maximum(y, 1), color=INK2, lw=0.6, label=tr("fig.measured"))
    if res.wp is not None:
        first = True
        for lab, xx, yy, ym in res.wp.curves:
            ax.plot(xx, np.maximum(ym, 1), color=BLUE, lw=1.0,
                    label=tr("fig.wp_model") if first else None)
            axr.plot(xx, yy - ym, color=INK2, lw=0.5)
            first = False
    if log:
        ax.set_yscale("log")
    ymax = np.max(y)
    for _, row in res.peaks.iterrows():
        ax.annotate(row["hkl"], (row["2theta"], ymax * (1.6 if log else 1.05)),
                    ha="center", va="bottom", fontsize=6.5, color=INK2, rotation=90)
    if getattr(res, "beta_peaks", None) is not None:
        for _, row in res.beta_peaks.iterrows():
            ax.annotate("β" + row["hkl"][1:], (row["2theta"], ymax * (1.6 if log else 1.05)),
                        ha="center", va="bottom", fontsize=6.5, color=ORANGE, rotation=90)
    ax.set_ylim(top=ymax * (8 if log else 1.25))
    ax.set_ylabel(tr("fig.intensity"))
    axr.axhline(0, color=MUTED, lw=0.5)
    axr.set_ylabel(tr("fig.difference"))
    axr.set_xlabel("2θ (°)")
    ax.legend(loc="upper left")
    ax.set_title(tr("fig.pattern_title", s=res.sample), loc="left")
    for a in (ax, axr):
        _style(a)
    ax.tick_params(labelbottom=False)
    return fig


def fig_wholeprofile(res, ncols=4):
    """Every fitted window: measured points, model and difference."""
    curves = res.wp.curves if res.wp is not None else []
    n = len(curves)
    nrows = int(np.ceil(n / ncols)) if n else 1
    fig = _fig(DOUBLE, 4.6 * CM * nrows)
    gs = fig.add_gridspec(nrows, ncols)
    for i, (lab, x, y, ym) in enumerate(curves):
        ax = fig.add_subplot(gs[i // ncols, i % ncols])
        ax.plot(x, y, "o", ms=1.6, mfc="none", mec=INK2, mew=0.4, label=tr("fig.measured"))
        ax.plot(x, ym, color=BLUE, lw=1.0, label=tr("fig.model"))
        off = y.min() - 0.08 * (y.max() - y.min())
        ax.plot(x, y - ym + off, color=MUTED, lw=0.5, label=tr("fig.difference"))
        ax.set_title(lab.replace("+", " + "), loc="left", fontsize=8)
        ax.set_xlabel("2θ (°)")
        if i % ncols == 0:
            ax.set_ylabel(tr("fig.counts"))
        _style(ax)
        if i == 0:
            ax.legend(loc="upper right", fontsize=6)
    if res.wp is not None:
        w = res.wp
        fig.suptitle(f"{res.sample}: ρ = {w.rho:.2e} m$^{{-2}}$, M* = {w.M_star:.2f}, "
                     f"Rwp = {w.rwp:.1f} %", fontsize=8.5, x=0.01, ha="left")
    return fig


def fig_mwh(res):
    """Modified Williamson-Hall: (a) dK vs K sqrt(C), (b) (dK^2 - alpha)/K^2 vs x."""
    m, t = res.mwh, res.peaks
    fig = _fig(DOUBLE, 6.5 * CM)
    ax1, ax2 = fig.subplots(1, 2)
    cfac = np.sqrt(np.clip(1 + m.q1 * m.x + m.q2 * m.x ** 2, 0, None))
    X = m.K * cfac
    ax1.plot(X, m.dK * 1e3, "o", ms=5, mfc=BLUE, mec="white", mew=0.8, zorder=3)
    xs = np.linspace(0, X.max() * 1.08, 100)
    ax1.plot(xs, np.sqrt(m.alpha + m.beta * xs ** 2) * 1e3, color=INK2, lw=1.0,
             label=tr("fig.mwh_fit", r2=m.r2))
    for xi, yi, lab in zip(X, m.dK * 1e3, t["hkl"]):
        ax1.annotate(lab, (xi, yi), xytext=(3, 3), textcoords="offset points", fontsize=6.5,
                     color=INK2)
    ax1.set_xlabel(r"$K\,\sqrt{1+q_1x+q_2x^2}$ (nm$^{-1}$)")
    ax1.set_ylabel(r"$\Delta K$ ($10^{-3}$ nm$^{-1}$)")
    ax1.set_xlim(left=0)
    ax1.set_ylim(bottom=0)
    ax1.legend(loc="upper left")
    _panel(ax1, "a")
    yv = (m.dK ** 2 - m.alpha) / m.K ** 2
    ax2.plot(m.x, yv * 1e6, "o", ms=5, mfc=BLUE, mec="white", mew=0.8, zorder=3)
    xs = np.linspace(0, max(m.x.max() * 1.1, 0.1), 100)
    ax2.plot(xs, m.beta * (1 + m.q1 * xs + m.q2 * xs ** 2) * 1e6, color=INK2, lw=1.0,
             label=f"$q_1$ = {m.q1:.2f}, $q_2$ = {m.q2:.2f}")
    for xi, yi, lab in zip(m.x, yv * 1e6, t["hkl"]):
        ax2.annotate(lab, (xi, yi), xytext=(3, 3), textcoords="offset points", fontsize=6.5,
                     color=INK2)
    ax2.set_xlabel(r"$x = \frac{2}{3}\,(l/Ka)^2$")
    ax2.set_ylabel(r"$(\Delta K^2-\alpha)/K^2$ ($10^{-6}$)")
    ax2.legend(loc="best")
    _panel(ax2, "b")
    for a in (ax1, ax2):
        _style(a)
    return fig


def fig_mwa(res, n_lines=6):
    """Voigt-based modified Warren-Averbach: (a) ln A vs K^2 b^2C, (b) Y/L^2 vs ln L."""
    w = res.mwa
    fig = _fig(DOUBLE, 6.5 * CM)
    ax1, ax2 = fig.subplots(1, 2)
    idx = np.unique(np.linspace(0, len(w.L) - 1, min(n_lines, len(w.L))).astype(int))
    shades = ["#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]
    xs = np.linspace(0, w.X.max() * 1.05, 50)
    for k, i in enumerate(idx):
        c = shades[int(k * (len(shades) - 1) / max(len(idx) - 1, 1))]
        ax1.plot(w.X, w.lnA[i], "o", ms=3.5, mfc=c, mec="white", mew=0.5)
        b = np.polyfit(w.X, w.lnA[i], 1)
        ax1.plot(xs, np.polyval(b, xs), color=c, lw=0.9)
        ax1.annotate(f"L = {w.L[i]:.0f} nm", (xs[-1], np.polyval(b, xs[-1])), xytext=(2, 0),
                     textcoords="offset points", fontsize=6, color=INK2, va="center")
    ax1.set_xlabel(r"$K^2\,\overline{b^2C}_{hkl}$")
    ax1.set_ylabel(r"$\ln A(L)$")
    _panel(ax1, "a")
    lnL = np.log(w.L)
    ax2.plot(lnL, w.Y / w.L ** 2 * 1e3, "o", ms=4.5, mfc=BLUE, mec="white", mew=0.7, zorder=3)
    ls = np.linspace(lnL.min(), lnL.max(), 50)
    ax2.plot(ls, (w.slope * ls + w.intercept) * 1e3, color=INK2, lw=1.0)
    txt = (f"ρ = 2s/π = {w.rho:.2e} m$^{{-2}}$" if w.slope > 0 else tr("fig.slope_invalid"))
    ax2.text(0.04, 0.95, f"{txt}\nR² = {w.r2:.3f}", transform=ax2.transAxes, va="top",
             fontsize=7, color=INK)
    ax2.set_xlabel(r"$\ln L$ (L, nm)")
    ax2.set_ylabel(r"$Y(L)/L^2$ ($10^{-3}$ nm$^{-2}$)")
    _panel(ax2, "b")
    for a in (ax1, ax2):
        _style(a)
    return fig


def attainable_hull(exclude=("S3",)):
    names = [n for n in TI_SUBSYSTEMS if n not in exclude]
    pts = np.array([[TI_SUBSYSTEMS[n][2], TI_SUBSYSTEMS[n][3]] for n in names])
    hull = ConvexHull(pts)
    return names, pts, pts[hull.vertices]


def fig_burgers(res):
    """(a) q1-q2 plane: attainable region of Ti slip systems and the measured q;
    (b) Burgers-vector fractions from each method."""
    fig = _fig(DOUBLE, 7.0 * CM)
    ax1, ax2 = fig.subplots(1, 2, width_ratios=[1.25, 1])
    names, pts, hull = attainable_hull()
    ax1.add_patch(Polygon(hull, closed=True, fc="#eef4fc", ec=BLUE, lw=0.8, zorder=0,
                          label=tr("fig.attainable")))
    for n, (a, b) in zip(names, pts):
        t = TI_SUBSYSTEMS[n][0]
        ax1.plot(a, b, "s", ms=4, mfc=TYPE_COLOR[t], mec="white", mew=0.5, zorder=2)
        ax1.annotate(n, (a, b), xytext=(3, 2), textcoords="offset points", fontsize=6,
                     color=INK2)
    P, T1, T2 = type_parabolas()
    for t in P:
        ax1.plot(T1[t], T2[t], "D", ms=6, mfc="white", mec=TYPE_COLOR[t], mew=1.4, zorder=3)
        ax1.annotate(TYPE_LABEL[t] + " " + tr("fig.avg"), (T1[t], T2[t]), xytext=(4, -9),
                     textcoords="offset points", fontsize=6.5, color=INK)
    marks = []
    if res.mwh_free is not None:
        marks.append((res.mwh_free.q1, res.mwh_free.q2, "o", INK, tr("fig.free_mwh")))
    marks.append((res.mwh.q1, res.mwh.q2, "^", BLUE, tr("fig.con_mwh")))
    if res.wp is not None:
        marks.append((res.wp.q1, res.wp.q2, "*", ORANGE, tr("fig.wp")))
    for a, b, mk, c, lab in marks:
        ax1.plot(a, b, mk, ms=8 if mk != "*" else 11, mfc=c, mec="white", mew=0.8,
                 zorder=4, label=lab)
    allx = np.r_[pts[:, 0], [m[0] for m in marks]]
    ally = np.r_[pts[:, 1], [m[1] for m in marks]]
    ax1.set_xlim(max(allx.min(), -5) - 0.3, min(allx.max(), 6) + 0.6)
    ax1.set_ylim(max(ally.min(), -5) - 0.3, min(ally.max(), 5) + 0.3)
    ax1.set_xlabel("$q_1$")
    ax1.set_ylabel("$q_2$")
    ax1.legend(loc="upper center", bbox_to_anchor=(0.5, -0.2), ncol=2, fontsize=6.5)
    _panel(ax1, "a")

    methods = []
    if res.wp is not None:
        methods.append((tr("fig.wp"), res.wp.h))
    methods.append((tr("fig.con_mwh"), res.population.h))
    if res.combos:
        c = res.combos["mean"]
        methods.append((tr("fig.comb", n=res.combos["n"]),
                        {"a": c["h_a"], "c": c["h_c"], "c+a": c["h_c+a"]}))
    y = np.arange(len(methods))[::-1]
    for yi, (lab, h) in zip(y, methods):
        left = 0.0
        for t in ("a", "c", "c+a"):
            v = max(h.get(t, 0.0), 0.0)
            ax2.barh(yi, v, left=left, height=0.55, color=TYPE_COLOR[t], edgecolor="white",
                     linewidth=1.5, label=TYPE_LABEL[t] if yi == y[0] else None)
            if v > 0.07:
                ax2.text(left + v / 2, yi, f"{v:.2f}", ha="center", va="center", fontsize=6.5,
                         color="white" if t != "c+a" else INK)
            left += v
    ax2.set_yticks(y, [m[0] for m in methods])
    ax2.set_xlim(0, 1)
    ax2.set_xlabel(tr("fig.h_axis"))
    ax2.legend(loc="upper center", bbox_to_anchor=(0.5, -0.22), ncol=3, fontsize=7)
    _panel(ax2, "b")
    for a in (ax1, ax2):
        _style(a)
    return fig


def fig_instrument(inst):
    """Instrument model: standard component widths vs K and fitted polynomials."""
    fig = _fig(SINGLE, 6.0 * CM)
    ax = fig.add_subplot()
    pts = inst.points or {}
    if pts:
        K = np.array(pts["K"])
        ax.plot(K, np.array(pts["wG"]) * 1e3, "o", ms=4, mfc=BLUE, mec="white", mew=0.6,
                label=tr("fig.gauss_std"))
        ax.plot(K, np.array(pts["wL"]) * 1e3, "s", ms=4, mfc=ORANGE, mec="white", mew=0.6,
                label=tr("fig.lorentz_std"))
        ks = np.linspace(K.min(), K.max(), 100)
    else:
        ks = np.linspace(3, 9, 100)
    ax.plot(ks, inst.wg(ks) * 1e3, color=BLUE, lw=1.0)
    ax.plot(ks, inst.wl(ks) * 1e3, color=ORANGE, lw=1.0)
    ax.plot(ks, inst.fwhm(ks) * 1e3, color=INK2, lw=1.0, ls="--", label=tr("fig.fwhm_model"))
    ax.set_xlabel("K (nm$^{-1}$)")
    ax.set_ylabel(tr("fig.width_axis"))
    ax.set_ylim(bottom=0)
    ax.legend(loc="upper left", fontsize=6.5)
    ax.set_title(tr("fig.inst_title"), loc="left")
    if getattr(inst, "standard", ""):
        from . import standards
        info = [standards.display_name(inst.standard).split(" (")[0]]
        if inst.wavelength:
            info.append(f"$\\lambda_1$ = {inst.wavelength[0]:.5f} Å")
        if inst.n_indexed is not None and inst.standard != "other":
            info.append(tr("fig.zero_short", z=inst.zero_shift_deg))
        info = [t.replace("₂", "$_2$").replace("₃", "$_3$").replace("₆", "$_6$") for t in info]
        top = max(float(np.max(inst.fwhm(ks))) * 1e3, ax.get_ylim()[1])
        ax.set_ylim(0, top * 1.45)
        ax.text(0.98, 0.97, "\n".join(info), transform=ax.transAxes, ha="right", va="top", fontsize=6.0,
                color=INK2, linespacing=1.3)
    _style(ax)
    return fig


def fig_compare(results, labels=None):
    """rho of every sample with its 95 % interval (log scale); upper limits as
    arrows; Voigt-mWA values as open markers for comparison."""
    fig = _fig(SINGLE * 1.25, 8.2 * CM)
    ax = fig.add_subplot()
    xs = np.arange(len(results))
    labels = labels or [r.sample for r in results]
    first_up = True
    for i, r in enumerate(results):
        lo, hi = r.wp_interval if r.wp is not None else (np.nan, np.nan)
        if r.wp is not None and r.wp.rho >= 2e13:
            ax.errorbar(i, r.wp.rho, yerr=[[r.wp.rho - lo], [hi - r.wp.rho]], fmt="o", ms=6,
                        mfc=BLUE, mec="white", mew=0.8, ecolor=BLUE, elinewidth=1.0, capsize=3,
                        zorder=3, label=tr("fig.wp95") if i == 0 else None)
            ax.annotate(f"{r.wp.rho:.1e}", (i, r.wp.rho), xytext=(7, -2),
                        textcoords="offset points", fontsize=6.5, color=INK)
        elif np.isfinite(hi):
            ax.annotate("", xy=(i, hi / 4), xytext=(i, hi),
                        arrowprops=dict(arrowstyle="-|>", color=BLUE, lw=1.0))
            ax.plot(i, hi, "_", ms=10, mew=1.5, color=BLUE,
                    label=tr("fig.upper") if first_up else None)
            ax.annotate(f"< {hi:.1e}", (i, hi), xytext=(7, 0), textcoords="offset points",
                        fontsize=6.5, color=INK)
            first_up = False
        if r.valid and np.isfinite(r.mwa.rho):
            ax.plot(i + 0.18, r.mwa.rho, "o", ms=5, mfc="none", mec=ORANGE, mew=1.0,
                    label=tr("fig.vmwa") if not any(
                        h.get_label().startswith("Voigt") for h in ax.lines) else None)
    ax.set_yscale("log")
    vals = []
    for r in results:
        vals += [v for v in (r.wp_interval if r.wp is not None else ()) if np.isfinite(v)]
        if r.wp is not None and r.wp.rho >= 2e13:
            vals.append(r.wp.rho)
        if r.valid and np.isfinite(r.mwa.rho):
            vals.append(r.mwa.rho)
    if vals:
        ax.set_ylim(min(vals) / 8, max(vals) * 2.5)
    ax.set_xticks(xs, labels)
    ax.set_xlim(-0.5, len(results) - 0.3)
    ax.set_ylabel(tr("fig.rho_axis"))
    ax.set_xlabel(tr("fig.sample_axis"))
    ax.grid(axis="y", color=GRID, lw=0.5, which="major")
    ax.set_axisbelow(True)
    if ax.get_legend_handles_labels()[0]:
        ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.2), ncol=1, fontsize=6.5)
    _style(ax)
    return fig


def fig_lattice(results, labels=None):
    """Lattice parameters of all samples: (a) alpha a, (b) alpha c, (c) c/a,
    (d) beta a; error bars are standard errors of the Cohen fit."""
    labels = labels or [r.sample for r in results]
    x = np.arange(len(results))
    g = lambda k: np.array([r.lattice.get(k, np.nan) for r in results], float)
    fig = _fig(DOUBLE, 5.6 * CM)
    axs = fig.subplots(1, 4)
    spec = [("a", "a_err", r"$\alpha$  a (Å)", BLUE), ("c", "c_err", r"$\alpha$  c (Å)", BLUE),
            ("ca", "ca_err", r"$\alpha$  c/a", BLUE), ("a_beta", "a_beta_err", r"$\beta$  a (Å)", ORANGE)]
    for ax, (k, e, lab, col), letter in zip(axs, spec, "abcd"):
        v, ev = g(k), g(e)
        ok = np.isfinite(v)
        if not ok.any():
            ax.text(0.5, 0.5, tr("fig.no_beta"), transform=ax.transAxes, ha="center", va="center",
                    fontsize=7, color=MUTED)
            ax.set_yticks([])
        ax.errorbar(x[ok], v[ok], yerr=np.where(np.isfinite(ev[ok]), ev[ok], 0), fmt="o-", ms=4.5, color=col,
                    mfc=col, mec="white", mew=0.6, capsize=2.5, lw=0.9)
        ax.set_xticks(x, labels, rotation=45 if len(x) > 4 else 0)
        ax.set_xlim(-0.5, len(x) - 0.5)
        ax.set_ylabel(lab)
        ax.ticklabel_format(axis="y", useOffset=False)
        from matplotlib.ticker import FormatStrFormatter, MaxNLocator
        ax.yaxis.set_major_locator(MaxNLocator(5))
        ax.yaxis.set_major_formatter(FormatStrFormatter("%.4f" if k == "ca" else "%.3f"))
        _panel(ax, letter)
        _style(ax)
    return fig


def fig_fourier_components(res, K_index=None):
    """Whitepaper figure: the three Fourier factors of one reflection."""
    from .wholeprofile import size_fourier, wilkens_fast, L_GRID
    from .contrast import x_param
    w = res.wp
    t = res.peaks
    i = int(np.argmax(t["K"].values)) if K_index is None else K_index
    K = t["K"].values[i]
    l = int(t["hkl"].values[i].split(".")[1])
    a_nm = res.lattice_a_A / 10
    x = x_param(l, K, a_nm)
    chkl = w.b2c_hk0 * (1 + w.q1 * x + w.q2 * x * x)
    L = L_GRID[1:400]
    AD = np.exp(-(np.pi / 2) * w.rho * 1e-18 * L ** 2 * wilkens_fast(L, w.Re_nm) * K ** 2 * chkl)
    AS = size_fourier(L, w.m_nm, w.sigma)
    from .instrument import InstrumentModel  # noqa: F401
    fig = _fig(SINGLE * 1.3, 6.2 * CM)
    ax = fig.add_subplot()
    ax.plot(L, AS, color=AQUA, label=tr("fig.AS"))
    ax.plot(L, AD, color=ORANGE, label=tr("fig.AD"))
    ax.plot(L, AS * AD, color=BLUE, lw=1.6, label=tr("fig.ASAD"))
    ax.set_xlabel(tr("fig.L_axis"))
    ax.set_ylabel("A(L)")
    ax.set_ylim(0, 1.02)
    ax.set_xlim(0, L.max())
    ax.legend(loc="upper right")
    ax.set_title(tr("fig.refl_title", hkl=t["hkl"].values[i], K=K), loc="left")
    _style(ax)
    return fig


def fig_wilkens():
    """Whitepaper figure: Wilkens f(eta) and its small-L logarithmic limit."""
    from .mwa import wilkens_f
    eta = np.logspace(-2, 1.3, 200)
    f = wilkens_f(eta, ETA_FACTOR)
    fig = _fig(SINGLE, 5.6 * CM)
    ax = fig.add_subplot()
    ax.plot(eta, f, color=BLUE, label="Wilkens f(η)")
    ax.plot(eta, np.log(ETA_FACTOR / eta), color=INK2, ls="--", lw=0.9,
            label=tr("fig.lnapprox"))
    ax.set_xscale("log")
    ax.set_ylim(-1, 5)
    ax.axhline(0, color=MUTED, lw=0.5)
    ax.set_xlabel(r"$\eta = (e^{7/4}/2)\,L/R_e$")
    ax.set_ylabel("f(η)")
    ax.legend(loc="upper right")
    _style(ax)
    return fig
