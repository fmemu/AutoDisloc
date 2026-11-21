# SPDX-License-Identifier: MIT
# AutoDisloc 2 - Copyright (c) 2026 Firat Memu
"""Modified Williamson-Hall analysis for hcp crystals.

    (Delta K)^2 = alpha + beta K^2 (1 + q1 x + q2 x^2),   alpha = (0.9/D)^2

alpha, beta, q1 and q2 are fitted together (Ungar et al. 1998, 2001;
HajyAkbary et al. 2015), instead of taking alpha from a separate classical
Williamson-Hall plot.
"""

from dataclasses import dataclass

import numpy as np
from scipy.optimize import least_squares

from .contrast import x_param


@dataclass
class MWHResult:
    alpha: float
    beta: float
    q1: float
    q2: float
    D_nm: float
    r2: float
    errors: dict
    x: np.ndarray
    K: np.ndarray
    dK: np.ndarray
    y_fit: np.ndarray        # fitted dK^2
    linearity_r2: float      # dK vs K*sqrt(1+q1x+q2x^2), Borbely 2022 check


def fit_mwh(K, dK, l, a_nm, alpha_fixed=None):
    K = np.asarray(K, float)
    dK = np.asarray(dK, float)
    x = x_param(l, K, a_nm)
    y = dK ** 2

    # start values: quadratic fit of y/K^2 vs x with alpha = 0
    c2, c1, c0 = np.polyfit(x, y / K ** 2, 2)
    beta0 = max(c0, 1e-12)
    p0 = [0.0 if alpha_fixed is None else alpha_fixed, beta0, c1 / beta0, c2 / beta0]

    def model(p):
        return p[0] + p[1] * K ** 2 * (1.0 + p[2] * x + p[3] * x ** 2)

    if alpha_fixed is None:
        lo, hi = [0.0, 1e-15, -50, -50], [np.inf, np.inf, 50, 50]
        res = least_squares(lambda p: (model(p) - y) / y.mean(), np.clip(p0, lo, hi),
                            bounds=(lo, hi))
        p = res.x
        J = res.jac
    else:
        lo, hi = [1e-15, -50, -50], [np.inf, 50, 50]
        f = lambda pp: (model([alpha_fixed, *pp]) - y) / y.mean()
        res = least_squares(f, np.clip(p0[1:], lo, hi), bounds=(lo, hi))
        p = np.r_[alpha_fixed, res.x]
        J = res.jac
    yfit = model(p)
    ss_res = float(np.sum((y - yfit) ** 2))
    ss_tot = float(np.sum((y - y.mean()) ** 2))
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0
    dof = max(len(y) - J.shape[1], 1)
    try:
        cov = np.linalg.pinv(J.T @ J) * (np.sum(res.fun ** 2) / dof)
        e = np.sqrt(np.clip(np.diag(cov), 0, None))
    except Exception:
        e = np.full(J.shape[1], np.nan)
    keys = ["alpha", "beta", "q1", "q2"] if alpha_fixed is None else ["beta", "q1", "q2"]
    errors = {k: float(v) for k, v in zip(keys, e)}
    D = 0.9 / np.sqrt(p[0]) if p[0] > 0 else np.inf
    cfac = np.sqrt(np.clip(1.0 + p[2] * x + p[3] * x ** 2, 0, None))
    lin = np.corrcoef(K * cfac, dK)[0, 1] ** 2 if len(K) > 2 else np.nan
    return MWHResult(float(p[0]), float(p[1]), float(p[2]), float(p[3]), float(D),
                     float(r2), errors, x, K, dK, yfit, float(lin))


def fit_mwh_population(K, dK, l, a_nm, exclude=("S3",), prismatic_weight=1.0):
    """mWH with the contrast written directly in terms of the Burgers-type
    fractions (Dragomir & Ungar 2002, Eqs. 10-13):

        (Delta K)^2 = alpha + K^2 sum_t g_t P_t (1 + q1_t x + q2_t x^2),
        g_t = beta' h_t >= 0,  alpha >= 0

    which is linear in (alpha, g_t) and solved by non-negative least squares.
    The fitted q1, q2 are therefore always attainable by Ti slip systems and
    h_t = g_t / sum g_t are proper fractions. When the free mWH q lies inside
    the attainable region both fits coincide.

    Returns (MWHResult, h dict, b2C_hk0). beta of the result is sum g_t P_t,
    i.e. the same quantity as in fit_mwh (coefficient of K^2 (1+q1x+q2x^2))."""
    from scipy.optimize import nnls
    from .contrast import type_parabolas
    K = np.asarray(K, float)
    dK = np.asarray(dK, float)
    x = x_param(l, K, a_nm)
    y = dK ** 2
    P, T1, T2 = type_parabolas(exclude, prismatic_weight)
    types = list(P)
    A = np.column_stack([np.ones_like(K)] + [K ** 2 * P[t] * (1 + T1[t] * x + T2[t] * x ** 2)
                                             for t in types])
    s = y.mean()
    coef, _ = nnls(A / s, y / s)
    alpha, g = coef[0], coef[1:]
    if g.sum() <= 0:
        raise ValueError("mWH: dislocation term is zero")
    h = dict(zip(types, map(float, g / g.sum())))
    b2c = sum(h[t] * P[t] for t in types)
    q1 = sum(h[t] * P[t] * T1[t] for t in types) / b2c
    q2 = sum(h[t] * P[t] * T2[t] for t in types) / b2c
    beta = float(g.sum() * b2c)
    yfit = A @ coef
    ss_res = float(np.sum((y - yfit) ** 2))
    ss_tot = float(np.sum((y - y.mean()) ** 2))
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0
    D = 0.9 / np.sqrt(alpha) if alpha > 0 else np.inf
    cfac = np.sqrt(np.clip(1.0 + q1 * x + q2 * x ** 2, 0, None))
    lin = np.corrcoef(K * cfac, dK)[0, 1] ** 2 if len(K) > 2 else np.nan
    res = MWHResult(float(alpha), beta, float(q1), float(q2), float(D), float(r2), {},
                    x, K, dK, yfit, float(lin))
    return res, h, float(b2c)
