"""Reproduction of published numbers (see docs/validation.md).

Run:  python -m pytest tests
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from autodisloc.contrast import (combinations, population_from_h,  # noqa: E402
                                 solve_population, type_parabolas)
from autodisloc.mwh import fit_mwh, fit_mwh_population  # noqa: E402


def _type_average_h(q1, q2, prismatic_weight=1.0):
    P, T1, T2 = type_parabolas(("S3",), prismatic_weight)
    t = list(P)
    p, a, b = (np.array([d[k] for k in t]) for d in (P, T1, T2))
    h = np.linalg.solve(np.array([p * (a - q1), p * (b - q2), np.ones(3)]), [0, 0, 1])
    return dict(zip(t, h)), float(h @ p)


def test_dragomir_2002_titanium():
    """Dragomir & Ungar 2002, Sec. 5.3: q1 = -0.05, q2 = 0.18 ->
    h = 75 +/- 10 %, 20 +/- 5 %, 5 +/- 3 %; b2C_hk0 = 0.0222 nm^2."""
    for w in (1.0, 2.0):
        h, b2c = _type_average_h(-0.05, 0.18, w)
        assert abs(h["a"] - 0.75) <= 0.10
        assert abs(h["c"] - 0.20) <= 0.05
        assert abs(h["c+a"] - 0.05) <= 0.04
    # step (iii), prismatic <a> double weight: b2C as published
    _, b2c = _type_average_h(-0.05, 0.18, 2.0)
    assert abs(b2c - 0.0222) < 0.0005
    # engine default reproduces the step (i) solution
    pop = solve_population(-0.05, 0.18)
    h1, b1 = _type_average_h(-0.05, 0.18, 1.0)
    assert pop.physical and abs(pop.b2c_hk0 - b1) < 1e-6


def test_muiruri_2020_table4_b2c():
    """Muiruri et al. 2020, Table 4: b2C_hk0 from the published h fractions
    with type-averaged contrast factors (Appendix A, Eq. A3)."""
    table4 = [((0.8800, 0, 0.1200), 0.0253), ((0.9088, 0, 0.0912), 0.0245),
              ((0.9077, 0, 0.0923), 0.0245), ((0.8819, 0, 0.1181), 0.0252),
              ((0.8925, 0, 0.1075), 0.0249)]
    P, _, _ = type_parabolas(exclude=())
    for (ha, hc, hca), b2c in table4:
        assert abs(ha * P["a"] + hc * P["c"] + hca * P["c+a"] - b2c) < 6e-5


def test_muiruri_2020_h_not_consistent_with_own_q():
    """The published h of Muiruri Table 4 do not reproduce the published q
    of Table 2 (documented, not a defect of this code)."""
    X, q1, q2 = population_from_h({"a": 0.88, "c": 0.0, "c+a": 0.12}, exclude=())
    assert abs(q1 - (-0.34)) > 0.1


def test_combinations_solve_dragomir_eqs_11_13():
    """One sub-system per Burgers type: 4 x 2 x 5 = 40 combinations; every
    solution satisfies Dragomir & Ungar 2002 Eqs. 11-13 (sum h = 1 and the
    measured q reproduced), and an attainable q has physical solutions."""
    from autodisloc.contrast import BURGERS_NM, TI_SUBSYSTEMS
    q = (-0.31, 0.05)
    rows = combinations(*q)
    assert len(rows) == 40
    for r in rows:
        names = (r["a"], r["c"], r["c+a"])
        h = np.array([r["h_a"], r["h_c"], r["h_c+a"]])
        P = np.array([TI_SUBSYSTEMS[n][1] * BURGERS_NM[TI_SUBSYSTEMS[n][0]] ** 2 for n in names])
        T1 = np.array([TI_SUBSYSTEMS[n][2] for n in names])
        T2 = np.array([TI_SUBSYSTEMS[n][3] for n in names])
        assert abs(h.sum() - 1) < 1e-9
        assert abs((h * P * T1).sum() / (h @ P) - q[0]) < 1e-9
        assert abs((h * P * T2).sum() / (h @ P) - q[1]) < 1e-9
        assert abs(r["b2C_hk0"] - h @ P) < 1e-12
    assert any(r["physical"] for r in rows)


def test_shintani_2010_mwh_alpha():
    """Shintani et al. 2010 (Mg AX52), Table 3 FWHMs: alpha = 4.29e-5 nm^-2,
    D = 137 nm is obtained only with Delta K = 2 cos(theta) FWHM(2theta) /
    lambda, i.e. twice the correct breadth. With the correct definition
    alpha is four times smaller (D twice as large); q does not change."""
    lam, a = 0.15405, 0.3209
    tt = np.array([34.47, 36.76, 57.71, 67.50, 70.20, 97.15])
    fw = np.array([0.0397, 0.0432, 0.0622, 0.0717, 0.0746, 0.115])
    l = np.array([2, 1, 0, 0, 1, 1])
    th = np.deg2rad(tt / 2)
    K = 2 * np.sin(th) / lam
    paper = fit_mwh(K, 2 * np.cos(th) * np.deg2rad(fw) / lam, l, a)
    right = fit_mwh(K, np.cos(th) * np.deg2rad(fw) / lam, l, a)
    assert abs(paper.alpha - 4.29e-5) / 4.29e-5 < 0.05
    assert abs(paper.D_nm - 137) < 5
    assert abs(right.alpha * 4 - paper.alpha) < 1e-9
    assert abs(right.q1 - paper.q1) < 1e-6


def test_constrained_mwh_equals_free_when_inside():
    """Constrained (h-parametrised) mWH = free mWH when q is attainable."""
    a = 0.295
    K = np.array([3.95, 4.29, 4.50, 5.83, 6.85, 7.55, 8.08, 8.19])
    l = np.array([0, 2, 1, 2, 0, 3, 2, 1])
    h = {"a": 0.7, "c": 0.2, "c+a": 0.1}
    b2c, q1, q2 = population_from_h(h)
    from autodisloc.contrast import x_param
    x = x_param(l, K, a)
    dK = np.sqrt(2e-5 + 0.05 * K ** 2 * b2c * (1 + q1 * x + q2 * x * x))
    free = fit_mwh(K, dK, l, a)
    con, hh, bb = fit_mwh_population(K, dK, l, a)
    assert abs(free.q1 - q1) < 1e-3 and abs(con.q1 - q1) < 1e-6
    assert all(abs(hh[t] - h[t]) < 1e-6 for t in h)
