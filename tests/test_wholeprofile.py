"""Whole-profile (Wilkens) fit: recovery of known parameters from a
synthetic Ti pattern generated with the example instrument model."""
import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from autodisloc import ti64  # noqa: E402
from autodisloc.instrument import InstrumentModel  # noqa: E402
from autodisloc.io import Pattern  # noqa: E402
from autodisloc.mwa import ETA_FACTOR  # noqa: E402
from autodisloc.wholeprofile import _Model, fit_whole_profile, size_fourier, wilkens_fast  # noqa: E402

INST = os.path.join(os.path.dirname(__file__), "..", "autodisloc", "data", "instrument_corundum_example.json")


def test_wilkens_fast_small_L_limit():
    L = np.array([0.1, 0.5, 1.0])
    assert np.allclose(wilkens_fast(L, 200.0), np.log(200.0 / L), atol=0.01)


def test_size_fourier_normalised():
    a = size_fourier(np.array([0.0, 1e5]), 100.0, 0.4)
    assert abs(a[0] - 1) < 1e-12 and abs(a[1]) < 1e-12


def _synthetic(rho, Re, m, u, seed):
    inst = InstrumentModel.load(INST)
    x = np.arange(20, 90, 0.02)
    pat = Pattern(two_theta=x, counts=np.zeros_like(x), wl1=1.540598, wl2=1.544426,
                  ka2_ratio=0.5, source="synth")
    mdl = _Model(pat, inst, None, ti64.ALPHA_A / 10, ("S3",), 1.0)
    h, b2c, q1, q2 = mdl.population(*u)
    glob = (rho * 1e-18, Re, m, 0.3, h, b2c, q1, q2)
    y = 200.0 + 0.5 * (x - 50)
    for lab, hh, kk, ll in ti64.ALPHA_REFLECTIONS:
        c = ti64.two_theta(ti64.d_hcp(hh, kk, ll, ti64.ALPHA_A, ti64.ALPHA_C), 1.540598)
        y = y + mdl.peak(x, c, 3000.0 * ti64.ICDD_ALPHA_INTENSITY.get(lab, 30) / 100, ll, glob)
    pat.counts = np.random.default_rng(seed).poisson(y).astype(float)
    return pat, inst, h


@pytest.mark.parametrize("rho,Re,u", [(3e15, 30.0, (-1.0, -2.0)), (2e14, 150.0, (-2.0, -1.0))])
def test_recovery(rho, Re, u):
    pat, inst, h = _synthetic(rho, Re, 150.0, u, 3)
    r = fit_whole_profile(pat, inst, start={"log_rho": 14.8})
    M_true = Re / ETA_FACTOR * np.sqrt(rho * 1e-18)
    assert abs(np.log10(r.rho / rho)) < 0.06          # within 15 %
    assert abs(r.M_star / M_true - 1) < 0.25
    assert abs(r.h["a"] - h[0]) < 0.08
    assert r.rwp < 5
