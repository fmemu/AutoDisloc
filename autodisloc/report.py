# SPDX-License-Identifier: MIT
# AutoDisloc 2 - Copyright (c) 2026 Firat Memu
"""Excel report of one or more analyses, in the active language."""

import os

import numpy as np
import pandas as pd

from ._meta import software
from .i18n import STRINGS, Msg, tr
from .pipeline import SUMMARY_KEYS

# column key -> help key
COLUMN_HELP = [
    ("rho", "help.rho"), ("rho_text", "help.rho_text"), ("rho_lo", "help.rho_lo"),
    ("interval_method", "help.interval_method"), ("M_star", "help.M_star"), ("Re_star_nm", "help.Re_star"), ("h_a", "help.h"),
    ("b2c_hk0", "help.b2c_hk0"), ("size_m_nm", "help.size"), ("chi2_dof", "help.gof"),
    ("mwa_rho", "help.mwa_rho"), ("mwa_Lmin", "help.mwa_L"), ("mwh_q1", "help.mwh"),
    ("free_q1", "help.free"), ("comb_h_a", "help.comb"), ("a_A", "help.lattice"),
]


def _plain(v):
    return str(v) if isinstance(v, Msg) else v


def summary_frame(results):
    """Localised summary table (one row per sample)."""
    rows = [{tr("col." + k): _plain(r.summary().get(k, "")) for k in SUMMARY_KEYS} for r in results]
    return pd.DataFrame(rows, columns=[tr("col." + k) for k in SUMMARY_KEYS])


def measurement_frame(results):
    """Measurement data and material settings of every sample (reproducibility)."""
    from .io import describe
    rows = []
    for r in results:
        p = r.pattern
        d = {tr("col.sample"): r.sample}
        if p is not None:
            d[tr("xl.file")] = os.path.basename(p.source or "")
            for k, v, _ in describe(p):
                d[tr("meta." + k)] = v
            d[tr("xl.assumed")] = ", ".join(p.assumed)
            u = p.meta.get("INTENSITY_UNIT", "counts")
            d[tr("xl.intensity")] = tr("iu." + u) if "iu." + u in STRINGS else u
        o = r.options
        if o is not None:
            d[tr("xl.material")] = o.material
            nom = getattr(r, "nominal", None) or o.nominal_lattice
            d[tr("xl.nominal")] = ", ".join(f"{v:.4f}" for v in nom)
        d[tr("xl.zero_applied")] = r.lattice.get("zero_shift_deg", 0.0) if r.lattice else ""
        rows.append(d)
    return pd.DataFrame(rows)


def write_excel(results, path, instrument=None):
    sheet = lambda tag, key: (tag + tr(key))[:31]
    with pd.ExcelWriter(path, engine="openpyxl") as xw:
        summary_frame(results).to_excel(xw, sheet_name=tr("xl.summary"), index=False)
        pd.DataFrame([(tr("col." + k), tr(h)) for k, h in COLUMN_HELP],
                     columns=[tr("xl.column"), tr("xl.meaning")]).to_excel(
            xw, sheet_name=tr("xl.columns")[:31], index=False)
        warn_rows = [{tr("col.sample"): r.sample, tr("xl.warning"): str(w)}
                     for r in results for w in r.warnings]
        pd.DataFrame(warn_rows or [{tr("col.sample"): "", tr("xl.warning"): tr("no_warnings")}]).to_excel(
            xw, sheet_name=tr("xl.warnings"), index=False)
        for i, r in enumerate(results):
            tag = f"{i + 1}_"
            r.peaks.to_excel(xw, sheet_name=sheet(tag, "xl.peaks"), index=False)
            m = r.mwa
            pd.DataFrame({"L (nm)": m.L, "Y(L)": m.Y, "Y/L2": m.Y / m.L ** 2,
                          "ln L": np.log(m.L), "R2 lnA-X": m.Y_r2}).to_excel(
                xw, sheet_name=(tag + "mWA")[:31], index=False)
            p = r.population
            rows = [{tr("xl.parameter"): k, tr("xl.value"): _plain(v)} for k, v in [
                (tr("xl.method"), p.method), ("b2Chk0", p.b2c_hk0), ("b2Chk0 min", p.b2c_min),
                ("b2Chk0 max", p.b2c_max), (tr("xl.q_physical"), p.physical),
                (tr("xl.q_residual"), p.residual), (tr("xl.q_reproduced"), str(p.q_reproduced)),
                (tr("xl.n_solutions"), p.n_solutions)]]
            rows += [{tr("xl.parameter"): f"h_{t}", tr("xl.value"): f"{p.h[t]:.3f} [{p.h_min[t]:.3f}-{p.h_max[t]:.3f}]"}
                     for t in p.h]
            rows += [{tr("xl.parameter"): f"f_{k}", tr("xl.value"): v} for k, v in p.fractions.items()]
            pd.DataFrame(rows).to_excel(xw, sheet_name=sheet(tag, "xl.burgers"), index=False)
            if getattr(r, "wp", None) is not None:
                rows = []
                for lab, x, y, ym in r.wp.curves:
                    rows += [{tr("xl.window"): lab, "2theta": a, tr("xl.measured"): b,
                              tr("xl.model"): c, tr("xl.diff"): b - c} for a, b, c in zip(x, y, ym)]
                pd.DataFrame(rows).to_excel(xw, sheet_name=sheet(tag, "xl.wp"), index=False)
            if r.texture:
                pd.DataFrame([{"hkl": k, "Harris T": v} for k, v in r.texture.items()]).to_excel(
                    xw, sheet_name=sheet(tag, "xl.texture"), index=False)
        measurement_frame(results).to_excel(xw, sheet_name=tr("xl.measurement")[:31], index=False)
        if instrument is not None:
            inst = instrument
            names = [tr("xl.inst_name"), tr("xl.gauss_coef"), tr("xl.lorentz_coef"), tr("xl.k_range")]
            vals = [inst.name, str(inst.gauss_coef), str(inst.lorentz_coef), str(inst.k_range)]
            if getattr(inst, "standard", ""):
                from . import standards
                names += [tr("xl.standard"), tr("xl.std_lattice")]
                vals += [standards.display_name(inst.standard), str(inst.lattice or "")]
            if getattr(inst, "wavelength", None):
                names.append(tr("xl.wavelength"))
                vals.append(", ".join(f"{v:.6g}" for v in inst.wavelength))
            if getattr(inst, "n_indexed", None) is not None:
                names += [tr("xl.zero"), tr("xl.std_disp"), tr("xl.indexed")]
                vals += [f"{inst.zero_shift_deg:+.4f} ± {inst.zero_err_deg or float('nan'):.4f}",
                         f"{inst.disp_um:.0f}" if inst.disp_um is not None else "",
                         f"{inst.n_indexed} / {inst.n_found}"]
            pd.DataFrame({tr("xl.parameter"): names, tr("xl.value"): vals}).to_excel(
                xw, sheet_name=tr("xl.instrument"), index=False)
            if instrument.points:
                pd.DataFrame({k: v for k, v in instrument.points.items()}).to_excel(
                    xw, sheet_name=tr("xl.instrument_peaks")[:31], index=False)
        # document properties: program name and version only
        wb = xw.book
        wb.properties.creator = software()
        wb.properties.lastModifiedBy = software()
