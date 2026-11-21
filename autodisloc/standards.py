# SPDX-License-Identifier: MIT
# AutoDisloc 2 - Copyright (c) 2026 Firat Memu
"""Line-profile standards: crystal data, peak indexing and the 2theta zero shift.

A standard serves two purposes:

1. its peak widths define the instrumental broadening (instrument.py);
2. its known lattice gives the true peak positions, so the observed positions
   yield the goniometer zero shift z and the specimen displacement s of the
   standard (Bragg-Brentano):

       2theta_obs - 2theta_calc = z - (360/pi) * s * cos(theta) / R

Indexing the observed peaks also rejects lines that do not belong to the
standard (impurity, K-beta or tungsten lines) and reveals a wrong wavelength
or a wrong standard choice (few peaks indexed).

The lattice parameters below are defaults. Certified values depend on the
batch and the temperature: enter the value of your certificate.
"""

from dataclasses import dataclass

import numpy as np


def _rule_r3c(h, k, l):
    """R-3c, hexagonal axes, obverse setting (corundum): -h+k+l = 3n; for
    h h-bar 0 l type reflections (h = -k, k = 0 or h = 0 in three-index
    notation) additionally l = 2n (c glide)."""
    if (-h + k + l) % 3:
        return False
    if (h == -k or k == 0 or h == 0) and l % 2:
        return False
    return True


def _rule_p(h, k, l):            # primitive cubic (LaB6, Pm-3m): no extinctions
    return True


def _rule_fcc(h, k, l):          # Fm-3m (CeO2 fluorite): h, k, l all even or all odd
    return h % 2 == k % 2 == l % 2


def _rule_diamond(h, k, l):      # Fd-3m (Si): fcc and, if all even, h+k+l = 4n
    if not _rule_fcc(h, k, l):
        return False
    return not (h % 2 == 0 and (h + k + l) % 4)


@dataclass(frozen=True)
class Standard:
    key: str
    name: str
    system: str                  # "hexagonal", "cubic" or "" (unknown)
    a: float = np.nan            # Angstrom
    c: float = np.nan
    source: str = ""
    rule: object = None


STANDARDS = {
    "corundum": Standard("corundum", "Corundum α-Al₂O₃ (R-3c)", "hexagonal", 4.7588, 12.9910,
                         "nominal (literature, e.g. ICDD PDF 00-046-1212); certificate value if available",
                         _rule_r3c),
    "LaB6": Standard("LaB6", "LaB₆ (Pm-3m)", "cubic", 4.156826, np.nan,
                     "NIST SRM 660c, certified at 22.5 °C", _rule_p),
    "Si": Standard("Si", "Si (Fd-3m)", "cubic", 5.431144, np.nan,
                   "NIST SRM 640f, certified at 22.5 °C", _rule_diamond),
    "CeO2": Standard("CeO2", "CeO₂ (Fm-3m)", "cubic", 5.4111, np.nan,
                     "nominal (NIST SRM 674a information value 5.411102 Å)", _rule_fcc),
    "other": Standard("other", "other / unknown", "", source="no indexing, no zero-shift calibration"),
}
STANDARD_KEYS = list(STANDARDS)


def _label(h, k, l):
    sep = " " if max(abs(h), abs(k), abs(l)) >= 10 else ""
    return sep.join(str(v) for v in (h, k, l))


def get(key):
    return STANDARDS.get(key, STANDARDS["other"])


def reflections(key, wl, a=None, c=None, tt_max=150.0):
    """Allowed reflections of a standard: sorted list of (2theta, label, d)."""
    std = get(key)
    if not std.system:
        return []
    a = float(a if a is not None else std.a)
    c = float(c if c is not None else std.c)
    d_min = wl / (2.0 * np.sin(np.deg2rad(tt_max / 2.0)))
    out = {}
    if std.system == "cubic":
        n = int(np.ceil(a / d_min)) + 1
        for h in range(n + 1):
            for k in range(h + 1):
                for l in range(k + 1):
                    s = h * h + k * k + l * l
                    if s == 0 or not std.rule(h, k, l):
                        continue
                    d = a / np.sqrt(s)
                    if d >= d_min:
                        out.setdefault(round(d, 6), _label(h, k, l))
    else:
        n = int(np.ceil(a / d_min)) + 1
        nl = int(np.ceil(c / d_min)) + 1
        cand = {}
        for h in range(-n, n + 1):
            for k in range(-n, n + 1):
                for l in range(-nl, nl + 1):
                    if h == k == l == 0 or not std.rule(h, k, l):
                        continue
                    d = 1.0 / np.sqrt(4.0 / 3.0 * (h * h + h * k + k * k) / a ** 2 + l * l / c ** 2)
                    if d >= d_min:
                        cand.setdefault(round(d, 6), []).append((h, k, l))
        for d, hkls in cand.items():
            # conventional representative: non-negative indices if possible, small h first
            pos = sorted([t for t in hkls if min(t) >= 0], key=lambda t: (-t[0], t[1], t[2])) or sorted(hkls, key=lambda t: (-min(t), t))
            out[d] = _label(*pos[0])
    res = []
    for d, lab in out.items():
        s = wl / (2.0 * d)
        if s < 1.0:
            res.append((2.0 * np.rad2deg(np.arcsin(s)), lab, d))
    return sorted(res)


def index_peaks(two_theta, key, wl, a=None, c=None, tol=0.10, max_offset=0.5):
    """Assign observed peak positions to reflections of the standard.

    A coarse search finds the constant offset (zero error) that indexes the
    most peaks; each peak is then assigned to the nearest reflection within
    ``tol`` of that offset. Returns (labels, calc_2theta) with None / NaN for
    peaks that are not indexed."""
    tt = np.asarray(two_theta, float)
    ref = reflections(key, wl, a, c, tt_max=min(float(tt.max()) + 2.0, 170.0)) if len(tt) else []
    if not ref:
        return [None] * len(tt), np.full(len(tt), np.nan)
    calc = np.array([r[0] for r in ref])
    best = (0, 0.0)
    for off in np.arange(-max_offset, max_offset + 1e-9, 0.005):
        dist = np.min(np.abs(tt[:, None] - off - calc[None, :]), axis=1)
        n = int(np.sum(dist < 0.05))
        if n > best[0] or (n == best[0] and abs(off) < abs(best[1])):
            best = (n, off)
    off = best[1]
    labels, out = [], np.full(len(tt), np.nan)
    used = set()
    for i in np.argsort(np.min(np.abs(tt[:, None] - off - calc[None, :]), axis=1)):
        j = int(np.argmin(np.abs(tt[i] - off - calc)))
        if abs(tt[i] - off - calc[j]) < tol and j not in used:
            used.add(j)
            out[i] = calc[j]
    lab_of = {r[0]: r[1] for r in ref}
    labels = [lab_of[v] if np.isfinite(v) else None for v in out]
    return labels, out


def zero_shift(two_theta_obs, two_theta_calc, radius_mm=250.0, weights=None):
    """Least-squares zero shift z (deg) and specimen displacement s (um) of the
    standard from obs - calc = z - (360/pi) s cos(theta)/R. With fewer than
    four peaks only z is fitted. Returns dict with values, errors and the rms
    residual (deg)."""
    o = np.asarray(two_theta_obs, float)
    cc = np.asarray(two_theta_calc, float)
    m = np.isfinite(o) & np.isfinite(cc)
    o, cc = o[m], cc[m]
    if len(o) < 2:
        return {"zero_deg": 0.0, "zero_err_deg": np.nan, "disp_um": np.nan, "disp_err_um": np.nan,
                "rms_deg": np.nan, "n": int(len(o))}
    y = o - cc
    cos_t = np.cos(np.deg2rad(cc / 2.0))
    fac = -360.0 / np.pi / radius_mm / 1000.0          # deg per um
    w = np.ones_like(y) if weights is None else np.asarray(weights, float)[m]
    if len(o) >= 4:
        A = np.column_stack([np.ones_like(y), fac * cos_t])
    else:
        A = np.ones((len(y), 1))
    Aw, yw = A * w[:, None], y * w
    sol, *_ = np.linalg.lstsq(Aw, yw, rcond=None)
    r = y - A @ sol
    dof = len(y) - A.shape[1]
    if dof > 0:
        s2 = float(np.sum((r * w) ** 2) / dof)
        cov = s2 * np.linalg.pinv(Aw.T @ Aw)
        err = np.sqrt(np.clip(np.diag(cov), 0, None))
    else:
        err = np.full(A.shape[1], np.nan)
    return {"zero_deg": float(sol[0]), "zero_err_deg": float(err[0]),
            "disp_um": float(sol[1]) if len(sol) > 1 else np.nan,
            "disp_err_um": float(err[1]) if len(sol) > 1 else np.nan,
            "rms_deg": float(np.sqrt(np.mean(r ** 2))), "n": int(len(y))}


def display_name(key):
    """Localised name (falls back to the table value)."""
    from .i18n import tr
    t = tr("std.name." + key)
    return get(key).name if t == "std.name." + key else t


def display_source(key):
    from .i18n import tr
    t = tr("std.src." + key)
    return get(key).source if t == "std.src." + key else t
