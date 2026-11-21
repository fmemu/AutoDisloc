# SPDX-License-Identifier: MIT
# AutoDisloc 2 - Copyright (c) 2026 Firat Memu
"""Intensities that are not raw counts, failed whole-profile fits, the name of
an instrument model and the M* convention."""
import os
import sys
from types import SimpleNamespace

import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from autodisloc import standards  # noqa: E402
from autodisloc.i18n import Msg, set_language  # noqa: E402
from autodisloc.instrument import InstrumentModel, fit_instrument  # noqa: E402
from autodisloc.io import ANODES, Pattern, intensity_unit, read_pattern  # noqa: E402
from autodisloc.peaks import ka2_position, voigt  # noqa: E402
from autodisloc.pipeline import AnalysisOptions, _whole_profile, measurement_warnings  # noqa: E402

ROOT = os.path.join(os.path.dirname(__file__), "..")
EXAMPLE = os.path.join(ROOT, "examples", "synthetic_Ti64_A.xy")
INST = InstrumentModel.load(os.path.join(ROOT, "autodisloc", "data", "instrument_corundum_example.json"))


def _keys(msgs):
    return [m.key for m in msgs if isinstance(m, Msg)]


# ------------------------------------------------------------ counts or not
def test_synthetic_example_is_raw_counts_without_warning():
    p = read_pattern(EXAMPLE)
    assert p.meta["INTENSITY_UNIT"] == "counts" and p.raw_counts
    assert "w.not_counts" not in _keys(measurement_warnings(p, INST))


def test_uxd_cps_is_flagged(tmp_path):
    x = np.arange(30.0, 31.0, 0.02)
    lines = ["_WL1=1.540598", "_WL2=1.544426", "_WLRATIO=0.5", "_2THETACPS"]
    lines += [f"{a:.3f} {b:.0f}" for a, b in zip(x, 500 + 100 * np.exp(-((x - 30.5) / 0.1) ** 2))]
    f = tmp_path / "s.uxd"
    f.write_text("\n".join(lines) + "\n", encoding="latin-1")
    p = read_pattern(str(f))
    assert p.meta["INTENSITY_UNIT"] == "cps" and not p.raw_counts
    w = [m for m in measurement_warnings(p, INST) if m.key == "w.not_counts"]
    assert len(w) == 1
    set_language("en")
    assert "raw counts" in str(w[0]) and "counts per second" in str(w[0])
    set_language("tr")
    assert "ham sayım" in str(w[0])
    set_language("en")


def test_scaled_and_low_intensities_are_flagged(tmp_path):
    x = np.arange(30.0, 31.0, 0.02)
    y = 1 + np.exp(-((x - 30.5) / 0.1) ** 2)          # normalised, non-integer
    f = tmp_path / "n.xy"
    f.write_text("\n".join(f"{a:.3f} {b:.6f}" for a, b in zip(x, y)), encoding="latin-1")
    assert read_pattern(str(f)).meta["INTENSITY_UNIT"] == "non-integer"
    assert intensity_unit([3, 5, 40]) == "low"
    assert intensity_unit([3, 5, 4000]) == "counts"
    assert intensity_unit([3, 5, 4000], declared="cps") == "cps"
    p = read_pattern(str(f))
    assert "w.not_counts" in _keys(measurement_warnings(p, INST))
    # the data themselves are not changed
    assert np.allclose(p.counts, y, atol=1e-6)


# ------------------------------------------------- whole-profile fit failures
def _res():
    return SimpleNamespace(warnings=[], wp=None, wp_interval=(np.nan, np.nan), wp_interval_method="")


def test_no_whole_profile_result_when_every_fit_fails(monkeypatch):
    import autodisloc.wholeprofile as wpm

    def fail(*a, **k):
        raise RuntimeError("boom")
    monkeypatch.setattr(wpm, "fit_whole_profile", fail)
    res = _res()
    _whole_profile(res, None, INST, AnalysisOptions())
    assert res.wp is None and np.all(np.isnan(res.wp_interval))
    assert "w.wp_no_result" in _keys(res.warnings)


def test_no_result_when_the_fixed_m_fit_fails(monkeypatch):
    """Free fit at the M* bound, every fixed-M* fit fails: no interval is
    fabricated and the free fit is not used."""
    import autodisloc.wholeprofile as wpm
    free = SimpleNamespace(warnings=[Msg("w.wp_bound", name="M*", value=10.0)], rho=1e15,
                           params={"chi2": 100.0, "log_rho_err": 0.01, "dof": 100})

    def fake(pattern, instrument, start=None, fix=None, **kw):
        if fix is None:
            return free
        raise RuntimeError("boom")
    monkeypatch.setattr(wpm, "fit_whole_profile", fake)
    res = _res()
    _whole_profile(res, None, INST, AnalysisOptions())
    keys = _keys(res.warnings)
    assert res.wp is None and np.all(np.isnan(res.wp_interval))
    assert "w.wp_no_result" in keys and "w.wp_fixed" in keys and "w.wp_fixed_ref" in keys


def test_no_result_when_a_band_end_fails(monkeypatch):
    import autodisloc.wholeprofile as wpm
    free = SimpleNamespace(warnings=[Msg("w.wp_bound", name="M*", value=10.0)], rho=1e15,
                           params={"chi2": 100.0, "log_rho_err": 0.01, "dof": 100})
    fixed = SimpleNamespace(warnings=[], rho=1e15, params={"chi2": 101.0, "log_rho_err": 0.01, "dof": 100})
    opts = AnalysisOptions()
    band_end = float(np.log10(opts.wp_M_band[1]))

    def fake(pattern, instrument, start=None, fix=None, **kw):
        if fix is None:
            return free
        if abs(fix["log_M"] - band_end) < 1e-12:
            raise RuntimeError("boom")
        return fixed
    monkeypatch.setattr(wpm, "fit_whole_profile", fake)
    res = _res()
    _whole_profile(res, None, INST, opts)
    assert res.wp is None and np.all(np.isnan(res.wp_interval))
    assert "w.wp_no_result" in _keys(res.warnings)


# ------------------------------------------------------------ instrument name
def test_instrument_model_name_is_the_file_name_not_the_path(tmp_path):
    wl1, wl2 = ANODES["Cu"]
    x = np.round(np.arange(20.0, 120.0 + 1e-9, 0.01), 4)
    y = np.full_like(x, 50.0)
    for t, _, _ in standards.reflections("LaB6", wl1, tt_max=118):
        y += voigt(x, t, 2000.0, 0.06, 0.036) + voigt(x, ka2_position(t, wl1, wl2), 1000.0, 0.06, 0.036)
    y = np.random.default_rng(0).poisson(y).astype(float)
    src = os.path.join(str(tmp_path), "some", "private", "folder", "LaB6_scan.xy")
    pat = Pattern(x, y, wl1, wl2, 0.5, src, {}, 250.0, fmt="test")
    inst = fit_instrument(pat, standard="LaB6")
    assert inst.name == "LaB6_scan.xy"
    out = tmp_path / "inst.json"
    inst.save(str(out))
    text = out.read_text(encoding="utf-8")
    assert "private" not in text and str(tmp_path) not in text


# ----------------------------------------------------------- M* convention
def test_m_star_conversion_to_the_cmwp_convention():
    """Ribarik et al. 2001 (MWP-fit): eta = (1/2) exp(-1/4) L / R_e*, M* = R_e* sqrt(rho),
    Re(ln form) = e^2 R_e*. The program evaluates f* at eta = L / Re*(program)."""
    from autodisloc.mwa import ETA_FACTOR, M_STAR_TO_CMWP, wilkens_f
    Re_ln, L = 60.0, np.array([0.5, 5.0, 30.0, 120.0, 400.0])
    re_star_cmwp = Re_ln / np.e ** 2
    eta_cmwp = 0.5 * np.exp(-0.25) * L / re_star_cmwp
    # same f* values: f*(eta_cmwp) evaluated directly (Re = ETA_FACTOR gives eta = L)
    assert np.allclose(wilkens_f(L, Re_ln), wilkens_f(eta_cmwp, ETA_FACTOR), rtol=1e-12)
    re_star_program = Re_ln / ETA_FACTOR
    assert re_star_program * M_STAR_TO_CMWP == pytest.approx(re_star_cmwp, rel=1e-12)
    assert 1 / M_STAR_TO_CMWP == pytest.approx(2.568, abs=5e-4)
