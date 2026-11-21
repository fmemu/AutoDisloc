# SPDX-License-Identifier: MIT
# AutoDisloc 2 - Copyright (c) 2026 Firat Memu
"""Physical whole-profile fit (Wilkens dislocation model), CMWP-type.

Instead of decomposing every peak into Voigt widths and building A(L) from
them (Voigt-based mWA), the measured profiles are fitted directly with the
physical Fourier coefficients (Ungar et al. 2001; Ribarik et al. 2001;
Dragomir & Ungar 2002):

    A(L) = A_S(L) * A_D(L) * A_I(L)

    A_S : volume-weighted log-normal spheres (median m, variance sigma)
    A_D = exp( -(pi/2) rho L^2 f*(eta) K^2 b^2C_hkl )      (Wilkens 1970)
          b^2C_hkl = b^2C_hk0(h) (1 + q1(h) x + q2(h) x^2)  (Dragomir 2002)
    A_I = exp( -pi L wL_s(K) - (pi^2/(4 ln2)) L^2 wG_s(K)^2 )  (standard)

I(s) = 2 int_0^inf A(L) cos(2 pi s L) dL, s = 2 sin(theta)/lambda - K, for
Ka1 and Ka2 (same physical profile, intensity ratio of the pattern).

Free parameters: rho, Re, m, sigma, two Burgers-type fractions (h_a, h_c,
h_c+a >= 0, sum 1), and per peak position and area, per window a linear
background. Peaks that are not used for the analysis (beta, 20.0, 20.2) are
free Voigt doublets.

Cut-off radius and arrangement parameter (conventions in mwa.py): the
program evaluates f* at eta = L / Re*, where Re* = Re / (e^1.75 / 2) =
Re / 2.877 and Re is the radius of the logarithmic form ln(Re/L) of the mWA
equation; it reports Re* and M* = Re* sqrt(rho). This is NOT the convention
of Wilkens/MWP-fit/CMWP (Ribarik, Ungar & Gubicza 2001, J. Appl. Cryst. 34,
669, Eq. 4 and Sec. 4: eta = (1/2) exp(-1/4) L / R_e*, M* = R_e* sqrt(rho),
Re = e^2 R_e*). The two differ by a constant factor:
    M*(CMWP) = M*(program) / (2 e^(1/4)) = M*(program) / 2.568,
and likewise for Re*. rho is the same in both conventions.
"""

from dataclasses import dataclass, field

import numpy as np
from scipy.optimize import least_squares

from . import ti64
from .contrast import BURGERS_NM, type_parabolas, x_param
from .i18n import Msg
from .mwa import ETA_FACTOR, GAUSS_FT, wilkens_f
from .peaks import MERGE_GAP, fit_group, make_windows, voigt, ka2_position

L_GRID = np.arange(0.0, 1500.5, 1.0)         # nm
_ETA = np.logspace(-4, 3, 1500)
_F = None
_GH_Z, _GH_W = np.polynomial.hermite_e.hermegauss(48)
_GH_W = _GH_W / _GH_W.sum()


def _f_table():
    global _F
    if _F is None:
        # wilkens_f takes (L, Re); with Re = ETA_FACTOR, eta = L
        _F = wilkens_f(_ETA, ETA_FACTOR)
    return _F


def wilkens_fast(L, Re):
    """f(L/Re) by interpolation; exact log limit below eta = 1e-4."""
    eta = ETA_FACTOR * np.asarray(L, float) / Re
    out = np.empty_like(eta)
    small = eta < _ETA[0]
    # for eta -> 0, f = -ln(eta) + 7/4 - ln 2 = ln(Re/L) with the scaling used
    out[small] = np.log(Re / np.maximum(np.asarray(L, float)[small], 1e-12))
    big = ~small
    out[big] = np.interp(np.log(eta[big]), np.log(_ETA), _f_table(), right=0.0)
    return out


def size_fourier(L, m, sigma):
    """Volume-weighted log-normal distribution of spheres (median m, nm)."""
    D = m * np.exp(3.0 * sigma ** 2 + sigma * _GH_Z)          # volume-weighted nodes
    t = np.asarray(L, float)[:, None] / D[None, :]
    a = np.where(t < 1.0, 1.0 - 1.5 * t + 0.5 * t ** 3, 0.0)
    return a @ _GH_W


def _h_from_u(u1, u2):
    e = np.exp([0.0, u1, u2])
    return e / e.sum()


@dataclass
class WholeProfileResult:
    rho: float                  # m^-2
    rho_err: float
    Re_nm: float                # radius of the ln(Re/L) form (mWA convention)
    Re_star_nm: float           # program convention: Re / 2.877 (CMWP R_e* = Re_star_nm / 2.568)
    M_star: float               # Re_star_nm * sqrt(rho)    (CMWP M* = M_star / 2.568)
    h: dict
    b2c_hk0: float
    q1: float
    q2: float
    m_nm: float
    sigma: float
    rwp: float
    success: bool
    params: dict = field(default_factory=dict)
    curves: list = field(default_factory=list)   # (label, x, y, model)
    warnings: list = field(default_factory=list)


class _Model:
    def __init__(self, pattern, instrument, reflections, a_nm, exclude, prismatic_weight):
        self.wl1 = pattern.wl1 / 10.0
        self.wl2 = pattern.wl2 / 10.0
        self.r2 = pattern.ka2_ratio
        self.inst = instrument
        self.a_nm = a_nm
        P, T1, T2 = type_parabolas(exclude, prismatic_weight)
        self.types = list(P)
        self.P = np.array([P[t] for t in self.types])
        self.T1 = np.array([T1[t] for t in self.types])
        self.T2 = np.array([T2[t] for t in self.types])
        self.reflections = reflections
        dL = np.diff(L_GRID)[0]
        self.wL = np.full(len(L_GRID), dL)
        self.wL[0] = self.wL[-1] = dL / 2

    def population(self, u1, u2):
        h = _h_from_u(u1, u2)
        b2c = float(h @ self.P)
        q1 = float(h @ (self.P * self.T1)) / b2c
        q2 = float(h @ (self.P * self.T2)) / b2c
        return h, b2c, q1, q2

    def peak(self, x, center, area, l, glob):
        """Ka1+Ka2 profile of one analysed reflection on the 2theta grid x."""
        rho_nm, Re, m, sig, h, b2c, q1, q2 = glob
        th0 = np.deg2rad(center / 2)
        K = 2 * np.sin(th0) / self.wl1
        xx = x_param(l, K, self.a_nm)
        chkl = b2c * (1 + q1 * xx + q2 * xx * xx)
        L = L_GRID
        lnA = -(np.pi / 2) * rho_nm * L ** 2 * wilkens_fast(np.maximum(L, 1e-9), Re) * K ** 2 * chkl
        lnA[0] = 0.0
        lnA += -np.pi * L * self.inst.wl(K) - GAUSS_FT * L ** 2 * self.inst.wg(K) ** 2
        A = size_fourier(L, m, sig) * np.exp(lnA) * self.wL
        th = np.deg2rad(x / 2)
        dsd2t = np.cos(th) / self.wl1 * np.pi / 180.0      # ds / d(2theta in deg)
        # the discrete cosine sum is periodic in s with period 1/dL: evaluate
        # only well inside the Nyquist range (the tails there are ~0)
        s_max = 0.4 / (L[1] - L[0])
        y = np.zeros_like(x, dtype=float)
        for lam, wgt in ((self.wl1, 1.0), (self.wl2, self.r2)):
            if wgt <= 0:
                continue
            s = 2 * np.sin(th) / lam - K
            ok = np.abs(s) < s_max
            y[ok] += wgt * (2 * np.cos(2 * np.pi * np.outer(s[ok], L)) @ A)
        return area * y * dsd2t


M_BOUNDS = (0.5, 10.0)


def fit_whole_profile(pattern, instrument, reflections=None, exclude=("S3",),
                      prismatic_weight=1.0, start=None, max_nfev=400, fix=None,
                      m_bounds=M_BOUNDS, nominal=None):
    """Fit the Wilkens model to all analysed alpha reflections together.

    The dislocation arrangement is parametrised by M* = Re* sqrt(rho) in the
    program's convention (module docstring; M*(CMWP) = M* / 2.568) and
    bounded to ``m_bounds``: for M* -> 0 the strain
    profile degenerates into a Lorentzian whose width fixes only the product
    rho*Re, so rho alone would be undetermined. ``fix`` = {"log_rho": v, ...}
    keeps parameters fixed (used for profile-likelihood limits). ``nominal`` =
    (a, c, a_beta) in Angstrom places the fit windows (default: Ti-6Al-4V)."""
    reflections = tuple(reflections or [r[0] for r in ti64.ALPHA_REFLECTIONS])
    x_all, y_all = pattern.two_theta, pattern.counts
    pos = [(t, k) for t, k in ti64.expected_positions(pattern.wl1, *(nominal or ()), with_beta=True)
           if x_all.min() + 0.5 < t < x_all.max() - 0.5]
    wins = make_windows(pos, x_all.min(), x_all.max(), half_width=1.0, merge_gap=MERGE_GAP)

    # Voigt pre-fit for start values (positions, areas, nuisance peaks, background)
    blocks, labels_used = [], []
    for gid, (a, b, group) in enumerate(wins):
        if not any(k in reflections for _, k in group):
            continue
        msk = (x_all >= a) & (x_all <= b)
        x, y = x_all[msk], y_all[msk]
        fits = fit_group(x, y, [g[0] for g in group], pattern.ka2_ratio, pattern.wl1,
                         pattern.wl2, 0.35, [g[1] for g in group], gid)
        expected = {g[1]: g[0] for g in group}
        keep = [f for f in fits if f.label in reflections
                or (f.area > 3 * (f.area_err if np.isfinite(f.area_err) else np.inf)
                    and not f.at_bound)]
        for f in keep:
            # a broad peak can be pulled onto a neighbour in the Voigt pre-fit
            if abs(f.center - expected[f.label]) > 0.15:
                f.center = expected[f.label]
        # background start from the window edges (robust for broad peaks)
        n = max(3, len(x) // 15)
        y0, y1 = np.median(y[:n]), np.median(y[-n:])
        x0, x1 = np.mean(x[:n]), np.mean(x[-n:])
        slope = (y1 - y0) / (x1 - x0)
        bg = (0.5 * (y0 + y1) + slope * (x.mean() - 0.5 * (x0 + x1)), slope)
        blocks.append({"x": x, "y": y, "bg": bg, "fits": keep})
        labels_used += [f.label for f in keep if f.label in reflections]

    hkls = [ti64.hkl_of(k) for k in labels_used]
    centers = [f.center for bl in blocks for f in bl["fits"] if f.label in reflections]
    a_A, c_A = ti64.fit_hcp_lattice(np.array(centers), hkls, pattern.wl1)
    model = _Model(pattern, instrument, reflections, a_A / 10.0, exclude, prismatic_weight)

    # parameter vector
    st = {"log_rho": 14.5, "log_M": 0.2, "log_m": 2.3, "sigma": 0.4, "u1": -1.0, "u2": -1.5}
    if start:
        st.update(start)
    if fix:
        st.update(fix)
    p0 = [st["log_rho"], st["log_M"], st["log_m"], st["sigma"], st["u1"], st["u2"]]
    lo = [11.0, np.log10(m_bounds[0]), 0.7, 0.05, -8, -8]
    hi = [17.5, np.log10(m_bounds[1]), 4.0, 1.2, 8, 8]
    layout = []
    for bl in blocks:
        p0 += list(bl["bg"])
        lo += [-np.inf, -np.inf]
        hi += [np.inf, np.inf]
        items = []
        for f in bl["fits"]:
            if f.label in reflections:
                items.append(("alpha", f.label, ti64.hkl_of(f.label)[2]))
                p0 += [f.center, max(f.area, 1.0)]
                lo += [f.center - 0.25, 0.0]
                hi += [f.center + 0.25, np.inf]
            else:
                items.append(("voigt", f.label, None))
                p0 += [f.center, max(f.area, 1e-3), max(f.wg, 2e-3), max(f.wl, 2e-3)]
                lo += [f.center - 0.15, 0.0, 1e-4, 1e-4]
                hi += [f.center + 0.15, np.inf, 3.0, 3.0]
        layout.append(items)
    p0 = np.clip(p0, np.array(lo) + 1e-9, np.array(hi) - 1e-9)

    def unpack_glob(p):
        h, b2c, q1, q2 = model.population(p[4], p[5])
        rho_nm = 10 ** p[0] * 1e-18
        Re = 10 ** p[1] / np.sqrt(rho_nm) * ETA_FACTOR      # ln-form Re from the program's M*
        return (rho_nm, Re, 10 ** p[2], p[3], h, b2c, q1, q2)

    def evaluate(p):
        glob = unpack_glob(p)
        k = 6
        out = []
        for bl, items in zip(blocks, layout):
            x = bl["x"]
            y = p[k] + p[k + 1] * (x - x.mean())
            k += 2
            for kind, lab, l in items:
                if kind == "alpha":
                    y = y + model.peak(x, p[k], p[k + 1], l, glob)
                    k += 2
                else:
                    c, ar, wg, wl = p[k:k + 4]
                    y = y + voigt(x, c, ar, wg, wl)
                    if model.r2 > 0:
                        y = y + model.r2 * voigt(x, ka2_position(c, pattern.wl1, pattern.wl2),
                                                 ar, wg, wl)
                    k += 4
            out.append(y)
        return out

    yobs = np.concatenate([bl["y"] for bl in blocks])
    w = 1.0 / np.sqrt(np.maximum(yobs, 1.0))

    names = ["log_rho", "log_M", "log_m", "sigma", "u1", "u2"]
    free = np.ones(len(p0), bool)
    for k in (fix or {}):
        free[names.index(k)] = False
    lo, hi = np.asarray(lo), np.asarray(hi)

    def full(pf):
        p = p0.copy()
        p[free] = pf
        return p

    def resid(pf):
        return (np.concatenate(evaluate(full(pf))) - yobs) * w

    res = least_squares(resid, p0[free], bounds=(lo[free], hi[free]), x_scale="jac",
                        max_nfev=max_nfev)
    p = full(res.x)
    rwp = 100 * np.sqrt(np.sum(res.fun ** 2) / np.sum((yobs * w) ** 2))
    dof = max(len(yobs) - int(free.sum()), 1)
    err = np.zeros(len(p))
    try:
        cov = np.linalg.pinv(res.jac.T @ res.jac) * (np.sum(res.fun ** 2) / dof)
        err[free] = np.sqrt(np.clip(np.diag(cov), 0, None))
    except Exception:
        err[free] = np.nan
    rho_nm, Re, m, sig, h, b2c, q1, q2 = unpack_glob(p)
    rho = rho_nm * 1e18
    Re_star = Re / ETA_FACTOR
    warn = []
    for name, i in (("rho", 0), ("M*", 1), ("m", 2), ("sigma", 3)):
        if free[i] and (p[i] <= lo[i] + 1e-4 or p[i] >= hi[i] - 1e-4):
            warn.append(Msg("w.wp_bound", name=name, value=10 ** p[i] if i < 3 else p[i]))
    curves = []
    model_y = evaluate(p)
    for bl, items, ym in zip(blocks, layout, model_y):
        curves.append(("+".join(l for _, l, _ in items), bl["x"], bl["y"], ym))
    return WholeProfileResult(
        rho=float(rho), rho_err=float(rho * np.log(10) * err[0]), Re_nm=float(Re),
        Re_star_nm=float(Re_star), M_star=float(Re_star * np.sqrt(rho_nm)),
        h=dict(zip(model.types, map(float, h))), b2c_hk0=b2c, q1=q1, q2=q2,
        m_nm=float(m), sigma=float(sig), rwp=float(rwp), success=bool(res.success),
        params={"log_rho_err": float(err[0]), "log_M_err": float(err[1]),
                "a_A": float(a_A), "c_A": float(c_A), "nfev": int(res.nfev),
                "chi2": float(np.sum(res.fun ** 2)), "n_points": int(len(yobs)),
                "dof": int(dof), "p": p.tolist()},
        curves=curves, warnings=warn)


def rho_profile(pattern, instrument, log_rho_values, best=None, fix=None, stop_delta=None, **kw):
    """Profile likelihood in rho: refit with rho fixed at each value. Returns
    (log_rho array, chi2 array). The 95 % interval is where
    chi2 - chi2_min < 3.84 * chi2_min/dof (chi2 scaled to the reduced
    chi-square of the best fit, because counting statistics alone
    underestimate the misfit of real profiles).

    Each point starts from the parameters of ``best`` (a WholeProfileResult)
    or of its neighbour, so that the scan follows one minimum instead of
    jumping between local minima. The scan runs outwards from the value
    closest to ``best``. With ``stop_delta`` a direction stops once
    chi2 - chi2_best exceeds stop_delta * chi2_best/dof (far beyond the 95 %
    threshold); the remaining points stay NaN."""
    names = ["log_rho", "log_M", "log_m", "sigma", "u1", "u2"]
    vals = np.asarray(log_rho_values, float)
    chi2 = np.full(len(vals), np.nan)

    def start_of(r):
        return dict(zip(names[1:], r.params["p"][1:6])) if r is not None else None

    i0 = int(np.argmin(np.abs(vals - np.log10(best.rho)))) if best is not None else 0
    for order in (range(i0, len(vals)), range(i0 - 1, -1, -1)):
        prev = best
        for i in order:
            st = start_of(prev)
            r = fit_whole_profile(pattern, instrument, start=st,
                                  fix={**(fix or {}), "log_rho": float(vals[i])}, **kw)
            chi2[i] = r.params["chi2"]
            prev = r
            if (stop_delta is not None and best is not None and chi2[i] - best.params["chi2"]
                    > stop_delta * best.params["chi2"] / best.params["dof"]):
                break
    return vals, chi2


def interval_from_profile(log_rho, chi2, chi2_best, dof):
    """95 % interval (m^-2) from a profile-likelihood scan; open ends -> None.
    The threshold crossing is interpolated linearly in log10(rho) between the
    scan points."""
    x, y = np.asarray(log_rho, float), np.asarray(chi2, float)
    keep = np.isfinite(y)
    order = np.argsort(x[keep])
    x, y = x[keep][order], y[keep][order]
    thr = chi2_best + 3.84 * chi2_best / dof
    ok = y <= thr
    if not ok.any():
        return None, None
    idx = np.where(ok)[0]
    i0, i1 = idx[0], idx[-1]
    lo = None if i0 == 0 else 10 ** float(np.interp(thr, [y[i0], y[i0 - 1]], [x[i0], x[i0 - 1]]))
    hi = None if i1 == len(x) - 1 else 10 ** float(np.interp(thr, [y[i1], y[i1 + 1]], [x[i1], x[i1 + 1]]))
    return lo, hi
