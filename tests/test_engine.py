import os
import sys

import numpy as np
import pytest
from scipy.special import voigt_profile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from autodisloc.contrast import solve_population, subsystem_range, contrast_hkl
from autodisloc.mwa import ln_fourier, mwa_from_lnA, run_mwa
from autodisloc.mwh import fit_mwh
from autodisloc.peaks import fit_group, voigt


def test_voigt_fourier_coefficients_match_numeric_transform():
    wg, wl = 0.02, 0.015                      # nm^-1
    K = np.linspace(-3, 3, 2 ** 20)
    dK = K[1] - K[0]
    I = voigt_profile(K, wg / (2 * np.sqrt(2 * np.log(2))), wl / 2)
    I /= I.sum() * dK
    L = np.array([5.0, 10.0, 20.0, 40.0])
    numeric = np.array([(I * np.cos(2 * np.pi * l * K)).sum() * dK for l in L])
    formula = np.exp(ln_fourier(L, [wg], [wl], "voigt")[:, 0])
    assert np.allclose(numeric, formula, rtol=2e-3)
    eq13 = np.exp(ln_fourier(L, [wg], [wl], "eq13")[:, 0])
    assert np.all(eq13 > numeric * 1.15)       # Muiruri 2020 Eq. 13 overestimates A(L)
    with pytest.raises(ValueError):
        ln_fourier(L, [wg], [wl], "unknown")   # an unknown mode is not accepted silently


def test_mwa_recovers_known_rho_and_Re():
    rho, Re, D = 5e14 * 1e-18, 60.0, 80.0      # nm^-2, nm, nm
    K = np.linspace(3.9, 8.2, 8)
    X = K ** 2 * np.linspace(0.015, 0.03, 8)   # K^2 b^2 C_hkl
    L = np.arange(2.0, 30.0, 1.0)
    lnA = -L[:, None] / D - rho * np.pi / 2 * L[:, None] ** 2 * np.log(Re / L[:, None]) * X[None, :]
    r = mwa_from_lnA(L, lnA, X)
    assert r.rho == pytest.approx(5e14, rel=1e-6)
    assert r.Re_nm == pytest.approx(60.0, rel=1e-6)
    assert r.rho_raw_slope == pytest.approx(5e14 * np.pi / 2, rel=1e-6)


def test_voigt_doublet_fit_recovers_widths():
    rng = np.random.default_rng(3)
    x = np.arange(39.0, 42.0, 0.02)
    y = 50 + voigt(x, 40.5, 400, 0.12, 0.10) + 0.5 * voigt(x, 40.6106, 400, 0.12, 0.10)
    y = rng.poisson(y * 10) / 10
    f = fit_group(x, y, [40.48], ka2=0.5, wl1=1.540598, wl2=1.544426)[0]
    assert f.center == pytest.approx(40.5, abs=0.005)
    assert f.wg == pytest.approx(0.12, rel=0.1)
    assert f.wl == pytest.approx(0.10, rel=0.1)


def test_mwh_recovers_parameters():
    K = np.array([3.96, 4.30, 4.50, 5.84, 6.85, 7.55, 8.08, 8.20])
    l = np.array([0, 2, 1, 2, 0, 3, 2, 1])
    a = 0.2925
    x = (2 / 3) * (l / (K * a)) ** 2
    alpha, beta, q1, q2 = 1e-4, 2.5e-5, -0.4, 0.05
    dK = np.sqrt(alpha + beta * K ** 2 * (1 + q1 * x + q2 * x ** 2))
    r = fit_mwh(K, dK, l, a)
    assert r.q1 == pytest.approx(q1, abs=1e-3)
    assert r.q2 == pytest.approx(q2, abs=1e-3)
    assert r.D_nm == pytest.approx(90.0, rel=1e-2)


def test_population_inside_and_outside_physical_region():
    # Muiruri 2020 sample A: q = (-0.34, 0.04) is attainable
    p = solve_population(-0.34, 0.04)
    assert p.physical
    assert 0.018 < p.b2c_hk0 < 0.03
    assert p.q_reproduced[0] == pytest.approx(-0.34, abs=1e-3)
    assert p.b2c_min <= p.b2c_hk0 <= p.b2c_max
    # q = (-0.908, 0.458) lies above the PrE-Pr2E hull edge (not attainable)
    assert subsystem_range(-0.908, 0.458) is None
    assert not solve_population(-0.908, 0.458).physical


def test_lp_range_brackets_every_mixture():
    rng = np.random.default_rng(0)
    from autodisloc.contrast import TI_SUBSYSTEMS, _table, _q_of
    names = [n for n in TI_SUBSYSTEMS if n != "S3"]
    w, Q1, Q2, _ = _table(names)
    for _ in range(20):
        f = rng.dirichlet(np.ones(len(names)))
        q = _q_of(f, w, Q1, Q2)
        r = subsystem_range(*q)
        assert r is not None
        assert r["b2c"][0] - 1e-9 <= (f * w).sum() <= r["b2c"][1] + 1e-9


def test_contrast_hkl_reduces_to_hk0_for_l0():
    assert contrast_hkl(0.025, -0.5, 0.1, [0.0])[0] == pytest.approx(0.025)


def test_wilkens_function_is_continuous_and_has_log_limit():
    from autodisloc.mwa import wilkens_f, ETA_FACTOR
    Re = 50.0
    L1 = 1.0 / ETA_FACTOR * Re
    a, b = wilkens_f([L1 * (1 - 1e-7), L1 * (1 + 1e-7)], Re)
    assert a == pytest.approx(b, abs=1e-5)
    small = wilkens_f([0.01], Re)[0]
    assert small == pytest.approx(np.log(Re / 0.01), abs=1e-3)
