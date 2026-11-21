# SPDX-License-Identifier: MIT
# AutoDisloc 2 - Copyright (c) 2026 Firat Memu
"""Voigt profile fitting of diffraction peaks.

Each peak is a Voigt function (Gaussian FWHM w_G, Lorentzian FWHM w_L are the
*component* widths, cf. HajyAkbary et al. 2015; Balzar & Ledbetter 1993).
If the pattern still contains Cu Ka2, every peak is fitted as a Ka1/Ka2
doublet with the Ka2 position from Bragg's law and fixed intensity ratio.
Overlapping peaks are fitted together with a shared linear background.
"""

from dataclasses import dataclass

import numpy as np
from scipy.optimize import least_squares
from scipy.signal import find_peaks
from scipy.special import voigt_profile

FWHM_MIN = 1e-4  # degrees 2theta
# expected peaks closer than this (deg 2theta) share one fit window; 1.5 keeps
# overlapping pairs such as alpha-Ti 11.2 / 20.1 (1.27-1.31 deg apart with Cu
# Ka, depending on the lattice) reliably in one window
MERGE_GAP = 1.5


def voigt(x, x0, area, wg, wl):
    """Area-normalised Voigt with Gaussian FWHM ``wg`` and Lorentzian FWHM ``wl``."""
    sigma = max(wg, 1e-9) / (2.0 * np.sqrt(2.0 * np.log(2.0)))
    gamma = max(wl, 1e-9) / 2.0
    return area * voigt_profile(x - x0, sigma, gamma)


def voigt_fwhm(wg, wl):
    """Olivero & Longbothum (1977) total FWHM of a Voigt."""
    return 0.5346 * wl + np.sqrt(0.2166 * wl ** 2 + wg ** 2)


def ka2_position(tt1, wl1, wl2):
    s = np.sin(np.deg2rad(tt1 / 2.0)) * wl2 / wl1
    return 2.0 * np.rad2deg(np.arcsin(np.clip(s, -1, 1)))


@dataclass
class PeakFit:
    label: str
    center: float          # Ka1 position, deg 2theta
    area: float
    wg: float              # Gaussian component FWHM, deg 2theta
    wl: float              # Lorentzian component FWHM, deg 2theta
    center_err: float = np.nan
    area_err: float = np.nan
    wg_err: float = np.nan
    wl_err: float = np.nan
    group: int = -1
    rwp: float = np.nan    # weighted profile R of the group fit, %
    at_bound: bool = False # a width hit its lower bound

    @property
    def fwhm(self):
        return voigt_fwhm(self.wg, self.wl)


def _group_model(p, x, n, ka2, wl1, wl2):
    y = p[0] + p[1] * (x - x.mean())
    for j in range(n):
        x0, area, wg, wl = p[2 + 4 * j: 6 + 4 * j]
        y = y + voigt(x, x0, area, wg, wl)
        if ka2 > 0:
            y = y + voigt(x, ka2_position(x0, wl1, wl2), ka2 * area, wg, wl)
    return y


def fit_group(x, y, guesses, ka2=0.0, wl1=1.540598, wl2=1.544426,
              max_shift=0.35, labels=None, group_id=0):
    """Fit several Voigt peaks (``guesses`` = list of 2theta) to x, y together.

    Returns a list of PeakFit in the order of ``guesses``.
    """
    n = len(guesses)
    labels = labels or [f"p{i}" for i in range(n)]
    bg0 = float(np.percentile(y, 5))
    p0 = [bg0, 0.0]
    lo = [-np.inf, -np.inf]
    hi = [np.inf, np.inf]
    for g in guesses:
        m = np.abs(x - g) < max_shift
        xg = x[m][np.argmax(y[m])] if m.any() else g
        h = max(float(y[m].max()) - bg0 if m.any() else 1.0, 1.0)
        # width guess: contiguous points above half maximum around the top
        i0 = int(np.argmin(np.abs(x - xg)))
        half = bg0 + 0.5 * h
        il, ir = i0, i0
        while il > 0 and y[il - 1] > half:
            il -= 1
        while ir < len(y) - 1 and y[ir + 1] > half:
            ir += 1
        step = float(np.median(np.diff(x)))
        fw = float(np.clip((ir - il + 1) * step, 2 * step, 1.5))
        area = h * fw * 1.2 / (1.0 + ka2)
        p0 += [xg, area, fw * 0.6, fw * 0.6]
        lo += [g - max_shift, 0.0, FWHM_MIN, FWHM_MIN]
        hi += [g + max_shift, np.inf, 3.0, 3.0]
    p0 = np.clip(p0, np.array(lo) + 1e-12, np.array(hi) - 1e-12)
    w = 1.0 / np.sqrt(np.maximum(y, 1.0))

    def resid(p):
        return (_group_model(p, x, n, ka2, wl1, wl2) - y) * w

    res = least_squares(resid, p0, bounds=(lo, hi), x_scale="jac", max_nfev=20000)
    p = res.x
    # standard errors from the Jacobian, scaled by reduced chi-square
    dof = max(len(x) - len(p), 1)
    chi2 = float(np.sum(res.fun ** 2)) / dof
    try:
        J = res.jac
        cov = np.linalg.pinv(J.T @ J) * chi2
        err = np.sqrt(np.clip(np.diag(cov), 0, None))
    except Exception:
        err = np.full(len(p), np.nan)
    rwp = 100.0 * np.sqrt(np.sum(res.fun ** 2) / np.sum((y * w) ** 2))
    fits = []
    for j in range(n):
        x0, area, wg, wl = p[2 + 4 * j: 6 + 4 * j]
        e = err[2 + 4 * j: 6 + 4 * j]
        at_bound = wg <= FWHM_MIN * 1.01 or wl <= FWHM_MIN * 1.01
        fits.append(PeakFit(labels[j], x0, area, wg, wl, e[0], e[1], e[2], e[3],
                            group_id, rwp, at_bound))
    return fits


def make_windows(positions, x_min, x_max, half_width=1.0, merge_gap=1.2):
    """Group expected peak positions (sorted list of (2theta, key)) into fit
    windows. Peaks closer than ``merge_gap`` share a window; each window is
    limited to the midpoint towards the neighbouring groups."""
    pos = sorted(positions)
    groups = []
    for tt, key in pos:
        if groups and tt - groups[-1][-1][0] < merge_gap:
            groups[-1].append((tt, key))
        else:
            groups.append([(tt, key)])
    windows = []
    for i, g in enumerate(groups):
        left = g[0][0] - half_width
        right = g[-1][0] + half_width
        if i > 0:
            left = max(left, 0.5 * (groups[i - 1][-1][0] + g[0][0]))
        if i < len(groups) - 1:
            right = min(right, 0.5 * (g[-1][0] + groups[i + 1][0][0]))
        windows.append((max(left, x_min), min(right, x_max), g))
    return windows


def find_and_fit_all(pattern, prominence=0.02, min_twotheta=None, max_twotheta=None):
    """Locate every peak above ``prominence`` x max and fit it (used for line
    standards such as corundum, LaB6, Si)."""
    x, y = pattern.two_theta, pattern.counts
    m = np.ones_like(x, bool)
    if min_twotheta is not None:
        m &= x >= min_twotheta
    if max_twotheta is not None:
        m &= x <= max_twotheta
    x, y = x[m], y[m]
    step = np.median(np.diff(x))
    # standard lines can be only 2-3 steps wide, so detect on the raw counts;
    # the minimum distance keeps noise on one peak top from being split
    idx, _ = find_peaks(y, prominence=prominence * (y.max() - y.min()),
                        distance=max(int(0.3 / step), 1))
    positions = [(float(x[i]), f"{x[i]:.2f}") for i in idx]
    ka2 = pattern.ka2_ratio
    # with Ka2 present, the doublet partner must not be found as a separate peak
    if ka2 > 0:
        kept = []
        for tt, key in positions:
            partner = [p for p in kept if abs(ka2_position(p[0], pattern.wl1, pattern.wl2) - tt) < 0.06]
            if not partner:
                kept.append((tt, key))
        positions = kept
    fits = []
    for gid, (a, b, group) in enumerate(make_windows(positions, x.min(), x.max(), 0.8, 0.9)):
        w = (x >= a) & (x <= b)
        if w.sum() < 10:
            continue
        fits += fit_group(x[w], y[w], [g[0] for g in group], ka2, pattern.wl1,
                          pattern.wl2, 0.2, [g[1] for g in group], gid)
    return fits
