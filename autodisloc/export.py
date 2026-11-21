# SPDX-License-Identifier: MIT
# AutoDisloc 2 - Copyright (c) 2026 Firat Memu
"""Paper package: every figure as PNG/TIFF (600 dpi), PDF and SVG, the Excel
report and the result table as CSV and LaTeX, in the active language."""

import os

import numpy as np
import pandas as pd

from . import figures as F
from ._meta import software
from .i18n import tr
from .report import write_excel


def export_package(results, folder, inst=None):
    os.makedirs(folder, exist_ok=True)
    figs = {tr("ex.compare"): F.fig_compare(results), tr("ex.lattice"): F.fig_lattice(results)}
    if inst is not None:
        figs[tr("ex.instrument")] = F.fig_instrument(inst)
    for r in results:
        s = r.sample
        figs[f"{s}_{tr('ex.pattern')}"] = F.fig_pattern(r)
        figs[f"{s}_3_mWH"] = F.fig_mwh(r)
        figs[f"{s}_4_mWA"] = F.fig_mwa(r)
        figs[f"{s}_{tr('ex.burgers')}"] = F.fig_burgers(r)
        if r.wp is not None:
            figs[f"{s}_{tr('ex.wp')}"] = F.fig_wholeprofile(r)
            figs[f"{s}_{tr('ex.fourier')}"] = F.fig_fourier_components(r)
    for name, fig in figs.items():
        for ext in ("png", "pdf", "svg", "tif"):
            sub = os.path.join(folder, tr("ex.figures"), ext)
            os.makedirs(sub, exist_ok=True)
            F.save_figure(fig, os.path.join(sub, f"{name}.{ext}"))
    write_excel(results, os.path.join(folder, tr("ex.report")), inst)
    table = paper_table(results)
    base = os.path.join(folder, tr("ex.table"))
    table.to_csv(base + ".csv", index=False, encoding="utf-8-sig")
    with open(base + ".tex", "w", encoding="utf-8") as f:
        f.write(latex_table(table))
    lat = lattice_table(results)
    base = os.path.join(folder, tr("ex.table_lattice"))
    lat.to_csv(base + ".csv", index=False, encoding="utf-8-sig")
    with open(base + ".tex", "w", encoding="utf-8") as f:
        f.write(latex_lattice(lat))


def lattice_table(results):
    rows = []
    for r in results:
        L = r.lattice
        rows.append({tr("ex.t_sample"): r.sample, "a_alpha (A)": L.get("a", np.nan), "a_alpha_err": L.get("a_err", np.nan),
                     "c_alpha (A)": L.get("c", np.nan), "c_alpha_err": L.get("c_err", np.nan),
                     "c/a": L.get("ca", np.nan), "c/a_err": L.get("ca_err", np.nan),
                     "a_beta (A)": L.get("a_beta", np.nan), "a_beta_err": L.get("a_beta_err", np.nan),
                     "displacement (um)": L.get("disp_um", np.nan)})
    return pd.DataFrame(rows)


def _pm(v, e, n=4):
    if not np.isfinite(v):
        return "--"
    if not np.isfinite(e) or e <= 0:
        return f"{v:.{n}f}"
    return f"{v:.{n}f}({int(round(e * 10 ** n))})"


def latex_lattice(t):
    s = (f"% {software()}\n\\begin{{table}}[htbp]\n\\centering\n\\caption{{"
         + tr("ex.tex_lattice_caption") + "}\n\\begin{tabular}{lllll}\n\\hline\n"
         + tr("ex.t_sample") + " & $a_\\alpha$ (\\AA) & $c_\\alpha$ (\\AA) & $c/a$ & $a_\\beta$ (\\AA) \\\\\n\\hline\n")
    for _, r in t.iterrows():
        s += (f"{r[tr('ex.t_sample')]} & {_pm(r['a_alpha (A)'], r['a_alpha_err'])} & {_pm(r['c_alpha (A)'], r['c_alpha_err'])} & "
              f"{_pm(r['c/a'], r['c/a_err'])} & {_pm(r['a_beta (A)'], r['a_beta_err'])} \\\\\n")
    return s + "\\hline\n\\end{tabular}\n\\end{table}\n"


def paper_table(results):
    rows = []
    for r in results:
        d = r.summary()
        if r.upper_limit_only:
            # no detectable dislocation broadening: the other parameters are undefined
            for k in ("M_star", "h_a", "h_c", "h_ca", "b2c_hk0"):
                d[k] = np.nan
        rows.append({
            tr("ex.t_sample"): r.sample,
            "rho (m^-2)": d["rho_text"],
            "M*": d["M_star"],
            "h_<a>": d["h_a"], "h_<c>": d["h_c"], "h_<c+a>": d["h_ca"],
            "b2C_hk0 (nm^2)": d["b2c_hk0"],
            "q1 (mWH)": d["mwh_q1"], "q2 (mWH)": d["mwh_q2"],
            "D (nm)": d["mwh_D_nm"],
            "chi2/dof": d["chi2_dof"],
        })
    return pd.DataFrame(rows)


def latex_table(t):
    head = (f"% {software()}\n"
            "\\begin{table}[htbp]\n\\centering\n\\caption{" + tr("ex.tex_caption") + "}\n"
            "\\begin{tabular}{lllllll}\n\\hline\n"
            + tr("ex.t_sample") + " & $\\rho$ (m$^{-2}$) & $M^*$ & $h_{\\langle a\\rangle}$ & "
            "$h_{\\langle c\\rangle}$ & $h_{\\langle c+a\\rangle}$ & "
            "$\\overline{b^2C}_{hk0}$ (nm$^2$) \\\\\n\\hline\n")
    body = ""
    for _, r in t.iterrows():
        rho = r["rho (m^-2)"]
        if rho.startswith("<"):
            rho_tex = "$<$ " + _sci(float(rho[1:]))
        elif rho.strip() == "-":
            rho_tex = "--"
        else:
            v, rest = rho.split(" (")
            lo, hi = rest.rstrip(")").split(" - ")
            rho_tex = f"{_sci(float(v))} ({_sci(float(lo))}--{_sci(float(hi))})"
        f = lambda x, n=2: "--" if not np.isfinite(x) else f"{x:.{n}f}"
        body += (f"{r[tr('ex.t_sample')]} & {rho_tex} & {f(r['M*'])} & {f(r['h_<a>'])} & "
                 f"{f(r['h_<c>'])} & {f(r['h_<c+a>'])} & {f(r['b2C_hk0 (nm^2)'], 4)} \\\\\n")
    return head + body + "\\hline\n\\end{tabular}\n\\end{table}\n"


def _sci(v):
    e = int(np.floor(np.log10(abs(v))))
    return f"${v / 10 ** e:.1f}\\times10^{{{e}}}$"
