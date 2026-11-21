# SPDX-License-Identifier: MIT
# AutoDisloc 2 - Copyright (c) 2026 Firat Memu
"""Modified Warren-Averbach analysis.

Fourier coefficients of a Voigt profile with component FWHMs w_G, w_L in
K units (nm^-1, K = 2 sin(theta)/lambda) and Fourier length L in nm:

    A(L) = exp( -pi L w_L - (pi^2 / (4 ln 2)) L^2 w_G^2 )            ("voigt")

(equivalent to exp(-2 L beta_C - pi L^2 beta_G^2) with integral breadths,
Balzar & Ledbetter 1993). The form exp(-(L^2 w_G^2 / 2 + L w_L)) of
Muiruri et al. 2020 Eq. 13 / HajyAkbary et al. 2015 Eq. 23 is available as
mode "eq13" for comparison with those papers.

mWA (Ungar & Borbely 1996):
    ln A(L) = ln A^S(L) - rho (pi b^2 / 2) L^2 ln(Re/L) (K^2 C_hkl)
Y(L) = slope of ln A(L) vs X = K^2 b^2C_hkl;
Y/L^2 = (rho pi/2) ln L - (rho pi/2) ln Re
  => rho = 2 s / pi,  Re = exp(-c / s).

Re here is the cut-off radius of the logarithmic form ln(Re/L) (Ungar et al.
2001, J. Appl. Cryst. 34, 298, Eq. 3, there called Re), and M = Re sqrt(rho)
(their Eq. 25a). See wilkens_f for the relation to the Wilkens/CMWP R_e*.
"""

from dataclasses import dataclass

import numpy as np
from scipy import stats

GAUSS_FT = np.pi ** 2 / (4.0 * np.log(2.0))


def ln_fourier(L, wg, wl, mode="voigt"):
    """ln A(L) matrix, shape (len(L), n_peaks)."""
    L = np.asarray(L, float)[:, None]
    wg = np.asarray(wg, float)[None, :]
    wl = np.asarray(wl, float)[None, :]
    if mode == "voigt":
        return -(np.pi * L * wl + GAUSS_FT * L ** 2 * wg ** 2)
    if mode == "eq13":
        # Muiruri et al. 2020 Eq. 13 / HajyAkbary et al. 2015 Eq. 23
        return -(0.5 * L ** 2 * wg ** 2 + L * wl)
    raise ValueError(f"unknown Fourier mode {mode!r} (use 'voigt' or 'eq13')")


@dataclass
class MWAResult:
    rho: float                 # m^-2 (2 s / pi)
    rho_raw_slope: float       # m^-2, the slope s itself (without the factor 2/pi)
    Re_nm: float
    M: float
    slope: float               # s, nm^-2
    intercept: float
    r2: float                  # of the Y/L^2 vs ln L line
    L: np.ndarray
    Y: np.ndarray
    Y_r2: np.ndarray           # R^2 of each ln A vs X regression
    X: np.ndarray
    lnA: np.ndarray
    n_positive_Y: int
    iterations: int


def mwa_from_lnA(L, lnA, X):
    """Core regression; L (nm), lnA (len(L) x n), X = K^2 b^2C_hkl (n)."""
    L = np.asarray(L, float)
    Y, R2 = [], []
    for row in lnA:
        r = stats.linregress(X, row)
        Y.append(r.slope)
        R2.append(r.rvalue ** 2)
    Y = np.array(Y)
    lin = stats.linregress(np.log(L), Y / L ** 2)
    s, c = lin.slope, lin.intercept
    rho_nm = 2.0 * s / np.pi
    Re = np.exp(-c / s) if s > 0 else np.nan
    M = Re * np.sqrt(rho_nm) if s > 0 else np.nan
    return MWAResult(rho_nm * 1e18, s * 1e18, Re, M, s, c, lin.rvalue ** 2, L, Y,
                     np.array(R2), np.asarray(X), lnA, int(np.sum(Y > 0)), 0)


def auto_L_grid(wg, wl, a_min=0.1, L_step=1.0, L_min=None, n_min=5, mode="voigt"):
    """Fourier lengths where every peak still has A(L) >= a_min."""
    L = np.arange(L_step, 500.0, L_step)
    A = np.exp(ln_fourier(L, wg, wl, mode)).min(axis=1)
    L = L[A >= a_min]
    if L_min is not None:
        L = L[L >= L_min]
    if len(L) < n_min:
        L = np.arange(1, n_min + 1) * L_step
    return L


def run_mwa(K, wg, wl, b2c_hkl, mode="voigt", L=None, a_min=0.1, L_step=1.0,
            limit_to_Re=True, max_iter=6):
    """mWA with automatic L range: A(L) >= a_min for all peaks and, if
    ``limit_to_Re``, L <= Re (small-L validity of the ln approximation)."""
    K = np.asarray(K, float)
    X = K ** 2 * np.asarray(b2c_hkl, float)
    if L is None:
        L = auto_L_grid(wg, wl, a_min, L_step, mode=mode)
    L = np.asarray(L, float)
    res = mwa_from_lnA(L, ln_fourier(L, wg, wl, mode), X)
    it = 0
    while limit_to_Re and it < max_iter and np.isfinite(res.Re_nm) and L.max() > res.Re_nm:
        L2 = L[L <= res.Re_nm]
        if len(L2) < 5:
            break
        L = L2
        res = mwa_from_lnA(L, ln_fourier(L, wg, wl, mode), X)
        it += 1
    res.iterations = it
    return res


# Wilkens (1970) strain function f*(eta), valid for all L, in the explicit
# form of Ribarik, Ungar & Gubicza 2001 (J. Appl. Cryst. 34, 669, Eq. 4;
# also Ungar et al. 2001, J. Appl. Cryst. 34, 298, Eqs. 22-23), quoting
# Wilkens 1970, Eqs. A6-A8. For small eta, f* -> -ln(eta) + 7/4 - ln 2.
#
# Conventions (all cut-off radii in nm):
#   Ribarik et al. 2001 (MWP-fit, CMWP):  eta = (1/2) exp(-1/4) L / R_e*,
#       M* = R_e* sqrt(rho); the radius of the ln form is Re = e^2 R_e*
#       (their text after Eq. 4; Ungar et al. 2001, Eq. 25: Re = 7.39 R_e').
#   This program:  eta = ETA_FACTOR * L / Re  with Re the radius of the ln
#       form, so f* -> ln(Re/L) for small L. The program's "Re*" is
#       Re / ETA_FACTOR (= L / eta), and its "M*" is Re* sqrt(rho).
#   Hence  R_e*(CMWP) = Re*(program) / (2 e^(1/4)) = Re*(program) / 2.568,
#          M*(CMWP)   = M*(program)  / 2.568,
#          M (Ungar et al. 2001, Re of the ln form) = 2.877 M*(program).
# The physics (and rho) is identical; only the reported arrangement
# parameter differs by these constant factors.
ETA_FACTOR = np.exp(1.75) / 2.0                 # = 2.8773
M_STAR_TO_CMWP = 1.0 / (2.0 * np.exp(0.25))     # M*(CMWP) = M*(program) * 0.3894


def wilkens_f(L, Re):
    """Wilkens f*(eta) with eta = ETA_FACTOR * L / Re (Re: radius of the
    ln(Re/L) form; see the conventions above)."""
    from scipy.integrate import quad
    eta = np.atleast_1d(ETA_FACTOR * np.asarray(L, float) / Re)
    out = np.empty_like(eta)
    for i, e in enumerate(eta):
        if e <= 1.0:
            I = quad(lambda v: np.arcsin(v) / v if v > 0 else 1.0, 0.0, e)[0]
            out[i] = (-np.log(e) + 7 / 4 - np.log(2) + 512 / (90 * np.pi * e)
                      + (2 / np.pi) * (1 - 1 / (4 * e * e)) * I
                      - (1 / np.pi) * (769 / (180 * e) + 41 * e / 90 + 2 * e ** 3 / 90) * np.sqrt(1 - e * e)
                      - (1 / np.pi) * (11 / (12 * e * e) + 7 / 2 + e * e / 3) * np.arcsin(e) + e * e / 6)
        else:
            out[i] = 512 / (90 * np.pi * e) - (11 / 24 + 0.25 * np.log(2 * e)) / (e * e)
    return out


SENSITIVITY_WINDOWS = {"L 2-10": np.arange(2.0, 11.0), "L 5-20": np.arange(5.0, 21.0),
                       "L 5-40 (Muiruri)": np.arange(5.0, 45.0, 5.0)}


def l_range_sensitivity(K, wg, wl, b2c_hkl, mode="voigt", windows=SENSITIVITY_WINDOWS):
    """rho and Re for fixed L windows; the spread is a model (L-range)
    uncertainty of the Voigt-based mWA and must be reported."""
    X = np.asarray(K) ** 2 * np.asarray(b2c_hkl)
    out = {}
    for name, L in windows.items():
        r = mwa_from_lnA(L, ln_fourier(L, wg, wl, mode), X)
        out[name] = (r.rho if r.slope > 0 else np.nan, r.Re_nm)
    return out
