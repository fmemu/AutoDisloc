# SPDX-License-Identifier: MIT
# AutoDisloc 2 - Copyright (c) 2026 Firat Memu
"""Instrumental broadening model from a line standard (corundum, LaB6, Si,
CeO2 or any other well-crystallised powder, see standards.py).

The Gaussian and Lorentzian component FWHMs of the standard, expressed in K
space (nm^-1), are each described by a polynomial in K. Sample widths are
corrected by (HajyAkbary et al. 2015, Eq. 21; Muiruri et al. 2020, Eq. 11)

    w_G,t^2 = w_G,m^2 - w_G,s^2,      w_L,t = w_L,m - w_L,s
"""

import json
import os
from dataclasses import dataclass, field, asdict, fields

import numpy as np

from ._meta import stamp

from . import standards
from .i18n import Msg, tr
from .io import read_pattern
from .peaks import find_and_fit_all, voigt_fwhm
from .ti64 import to_k


@dataclass
class InstrumentModel:
    gauss_coef: list            # numpy.polyval order, w_G,s(K) in nm^-1
    lorentz_coef: list          # w_L,s(K)
    k_range: tuple = (0.0, 20.0)
    name: str = "custom"
    points: dict = field(default_factory=dict)   # K, wG, wL of the standard peaks
    # measurement and calibration data of the standard (empty in old files)
    standard: str = ""                 # key of standards.STANDARDS ("" = not recorded)
    lattice: dict = field(default_factory=dict)  # a, c (Angstrom) used for indexing
    wavelength: list = None            # [wl1, wl2, Ka2/Ka1] of the standard measurement
    radius_mm: float = None
    zero_shift_deg: float = 0.0        # 2theta_obs - 2theta_true at the goniometer zero
    zero_err_deg: float = None
    disp_um: float = None              # specimen displacement of the standard
    n_indexed: int = None
    n_found: int = None

    def wg(self, K):
        return np.maximum(np.polyval(self.gauss_coef, K), 0.0)

    def wl(self, K):
        return np.maximum(np.polyval(self.lorentz_coef, K), 0.0)

    def fwhm(self, K):
        return voigt_fwhm(self.wg(K), self.wl(K))

    def save(self, path):
        d = asdict(self)
        d["_generator"] = stamp()
        with open(path, "w", encoding="utf-8") as f:
            json.dump(d, f, indent=2, ensure_ascii=False)

    @classmethod
    def load(cls, path):
        with open(path, encoding="utf-8") as f:
            d = json.load(f)
        names = {f.name for f in fields(cls)}
        d = {k: v for k, v in d.items() if k in names}
        d["k_range"] = tuple(d.get("k_range", (0, 20)))
        return cls(**d)

    def describe(self):
        """Lines for display: standard, wavelength, zero shift."""
        out = []
        if self.standard:
            out.append(standards.display_name(self.standard))
        if self.wavelength:
            out.append(f"λ₁ = {self.wavelength[0]:.5f} Å, Kα2/Kα1 = {self.wavelength[2]:.2f}")
        if self.n_indexed is not None and self.standard != "other":
            z = f"{self.zero_shift_deg:+.3f}°"
            if self.zero_err_deg is not None and np.isfinite(self.zero_err_deg):
                z += f" ± {self.zero_err_deg:.3f}°"
            out.append(tr("inst.zero", z=z, n=self.n_indexed, m=self.n_found))
        return out


def fit_instrument(pattern_or_path, degree=1, prominence=0.02, name=None,
                   min_twotheta=None, max_twotheta=None, ka2_stripped=None,
                   standard="other", lattice=None, radiation=None, radius_mm=None):
    """Fit Voigt peaks of a line standard and return an InstrumentModel.

    standard : key of standards.STANDARDS. With a known standard the peaks
               are indexed with ``lattice`` (default: the table value), peaks
               that are not reflections of the standard are discarded and
               the zero shift is determined. "other" uses every peak found.
    The returned model has the attribute ``fit_warnings`` (list of Msg)."""
    pat = pattern_or_path
    if isinstance(pattern_or_path, str):
        pat = read_pattern(pattern_or_path, ka2_stripped=ka2_stripped, radiation=radiation, radius_mm=radius_mm)
    warn = []
    if "wavelength" in getattr(pat, "assumed", []):
        warn.append(Msg("w.wl_assumed", wl=pat.wl1))
    fits = find_and_fit_all(pat, prominence, min_twotheta, max_twotheta)
    # reject failed fits: a component pinned at the lower bound is fine for a
    # standard (nearly pure Gaussian lines), a total width far from the
    # typical one or a poor profile R is not
    fits = [f for f in fits if f.area > 0 and np.isfinite(f.rwp)]
    n_found = len(fits)
    std = standards.get(standard)
    lat = dict(lattice or {})
    labels, calc, zs = [None] * len(fits), np.full(len(fits), np.nan), None
    if std.system and fits:
        lat = {"a": float(lat.get("a", std.a)), "c": float(lat.get("c", std.c))}
        labels, calc = standards.index_peaks([f.center for f in fits], std.key, pat.wl1,
                                             lat["a"], lat["c"])
        idx = [i for i, l in enumerate(labels) if l is not None]
        if len(idx) < 0.6 * n_found:
            warn.append(Msg("w.std_mismatch", n=len(idx), m=n_found, std=standards.display_name(std.key), wl=pat.wl1))
        if len(idx) >= degree + 2:
            dropped = [f"{fits[i].center:.2f}°" for i in range(len(fits)) if labels[i] is None]
            if dropped:
                warn.append(Msg("w.std_unindexed", peaks=", ".join(dropped)))
            fits = [fits[i] for i in idx]
            calc = calc[idx]
            labels = [labels[i] for i in idx]
            zs = standards.zero_shift([f.center for f in fits], calc, pat.radius_mm)
    med = np.median([f.fwhm for f in fits]) if fits else np.nan
    keep = [i for i, f in enumerate(fits) if 0.5 * med < f.fwhm < 2.0 * med]
    fits = [fits[i] for i in keep]
    labels = [labels[i] for i in keep]
    if len(fits) < degree + 2:
        raise ValueError(tr("w.std_few"))
    tt = np.array([f.center for f in fits])
    K, wg = to_k(tt, [f.wg for f in fits], pat.wl1_nm)
    _, wl = to_k(tt, [f.wl for f in fits], pat.wl1_nm)
    # robust fit: drop points more than 3 MAD from a first polynomial fit
    def robust(y):
        c = np.polyfit(K, y, degree)
        r = y - np.polyval(c, K)
        mad = np.median(np.abs(r - np.median(r))) * 1.4826 + 1e-12
        keep = np.abs(r) < 3 * mad
        if keep.sum() >= degree + 2:
            c = np.polyfit(K[keep], y[keep], degree)
        return c, keep
    cg, kg = robust(wg)
    cl, kl = robust(wl)
    pts = {"two_theta": tt.tolist(), "K": K.tolist(), "wG": wg.tolist(),
           "wL": wl.tolist(), "used_G": kg.tolist(), "used_L": kl.tolist()}
    if any(l is not None for l in labels):
        pts["hkl"] = [l or "" for l in labels]
    fin = lambda v: float(v) if v is not None and np.isfinite(v) else None
    # default name: file name of the standard, never its full path (the model
    # is saved to JSON and may be shared)
    default_name = os.path.basename(getattr(pat, "source", "") or "") or "standard"
    inst = InstrumentModel(
        gauss_coef=[float(v) for v in cg],
        lorentz_coef=[float(v) for v in cl],
        k_range=(float(K.min()), float(K.max())),
        name=name or default_name,
        points=pts,
        standard=std.key,
        lattice=lat if std.system else {},
        wavelength=[float(pat.wl1), float(pat.wl2), float(pat.ka2_ratio)],
        radius_mm=float(pat.radius_mm),
        zero_shift_deg=float(zs["zero_deg"]) if zs else 0.0,
        zero_err_deg=fin(zs["zero_err_deg"]) if zs else None,
        disp_um=fin(zs["disp_um"]) if zs else None,
        n_indexed=int(zs["n"]) if zs else None,
        n_found=int(n_found),
    )
    inst.fit_warnings = warn
    return inst


def correct(K, wg_m, wl_m, inst):
    """Instrument-corrected component widths (nm^-1) and a per-peak flag dict."""
    wgs, wls = inst.wg(K), inst.wl(K)
    g2 = wg_m ** 2 - wgs ** 2
    wg_t = np.sqrt(np.maximum(g2, 0.0))
    wl_t = np.maximum(wl_m - wls, 0.0)
    ratio = voigt_fwhm(wg_m, wl_m) / np.maximum(voigt_fwhm(wgs, wls), 1e-12)
    flags = {
        # set to zero either way; flagged only when clearly below the standard
        "gauss_negative": wg_m < 0.8 * wgs,
        "lorentz_negative": wl_m < wls - 0.2 * np.maximum(wgs, wls),
        "ratio": ratio,
        "outside_standard_range": (K < inst.k_range[0] - 0.3) | (K > inst.k_range[1] + 0.3),
    }
    return wg_t, wl_t, flags
