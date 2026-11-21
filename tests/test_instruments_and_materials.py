# SPDX-License-Identifier: MIT
# AutoDisloc 2 - Copyright (c) 2026 Firat Memu
"""Other instruments, standards and materials: file metadata (XRDML, xy
header), radiation overrides, indexing and zero shift of line standards,
other wavelengths and other titanium alloys."""
import json
import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from autodisloc import materials, standards, ti64
from autodisloc.instrument import InstrumentModel, fit_instrument
from autodisloc.io import ANODES, Pattern, read_pattern
from autodisloc.peaks import ka2_position, voigt
from autodisloc.pipeline import AnalysisOptions, fit_alpha_peaks, nominal_lattice, phase_lattice

HERE = os.path.dirname(__file__)
ROOT = os.path.dirname(HERE)


def _pattern(peaks, wl1, wl2, ratio=0.5, x0=20.0, x1=100.0, step=0.01, bg=50.0, seed=0, w=0.06):
    """Pattern with Voigt Ka1/Ka2 doublets at the given (Ka1 2theta, area) peaks."""
    x = np.round(np.arange(x0, x1 + 1e-9, step), 4)
    y = np.full_like(x, bg)
    for c, a in peaks:
        y += voigt(x, c, a, w, w * 0.6)
        if ratio:
            y += voigt(x, ka2_position(c, wl1, wl2), ratio * a, w, w * 0.6)
    y = np.random.default_rng(seed).poisson(y).astype(float)
    return Pattern(x, y, wl1, wl2, ratio, "synthetic", {}, 250.0, fmt="test")


# ------------------------------------------------------------------ readers
XRDML = """<?xml version="1.0" encoding="UTF-8"?>
<xrdMeasurements xmlns="http://www.xrdml.com/XRDMeasurement/1.5" status="Completed">
  <xrdMeasurement measurementType="Scan" status="Completed">
    <usedWavelength intended="K-Alpha 1 and 2">
      <kAlpha1 unit="Angstrom">1.7890100</kAlpha1>
      <kAlpha2 unit="Angstrom">1.7928500</kAlpha2>
      <kBeta unit="Angstrom">1.6208000</kBeta>
      <ratioKAlpha2KAlpha1>0.5000</ratioKAlpha2KAlpha1>
    </usedWavelength>
    <incidentBeamPath><radius unit="mm">240.00</radius>
      <xRayTube name="Co LFF"><anodeMaterial>Co</anodeMaterial></xRayTube></incidentBeamPath>
    <scan appendNumber="0" mode="Continuous" scanAxis="Gonio" status="Completed">
      <dataPoints>
        <positions axis="2Theta" unit="deg"><startPosition>30.00</startPosition><endPosition>30.04</endPosition></positions>
        <positions axis="Omega" unit="deg"><startPosition>15.00</startPosition><endPosition>15.02</endPosition></positions>
        <commonCountingTime unit="seconds">1.0</commonCountingTime>
        <counts unit="counts">10 20 30 40 50</counts>
      </dataPoints>
    </scan>
  </xrdMeasurement>
</xrdMeasurements>
"""


def test_xrdml_metadata_and_data(tmp_path):
    f = tmp_path / "co.xrdml"
    f.write_text(XRDML, encoding="utf-8")
    p = read_pattern(str(f))
    assert p.fmt == "PANalytical XRDML"
    assert p.wl1 == pytest.approx(1.78901) and p.wl2 == pytest.approx(1.79285)
    assert p.ka2_ratio == 0.5 and p.radius_mm == 240.0 and p.anode == "Co"
    assert p.assumed == []
    assert np.allclose(p.two_theta, [30.0, 30.01, 30.02, 30.03, 30.04])
    assert np.allclose(p.counts, [10, 20, 30, 40, 50])


def test_xrdml_alpha1_only_means_no_ka2(tmp_path):
    f = tmp_path / "a1.xrdml"
    f.write_text(XRDML.replace('intended="K-Alpha 1 and 2"', 'intended="K-Alpha 1"'), encoding="utf-8")
    assert read_pattern(str(f)).ka2_ratio == 0.0


def test_xy_header_and_assumptions(tmp_path):
    data = "\n".join(f"{30 + 0.02 * i:.2f} {100 + i}" for i in range(50))
    plain = tmp_path / "plain.xy"
    plain.write_text(data)
    p = read_pattern(str(plain))
    assert set(p.assumed) == {"wavelength", "ka2", "radius"} and p.wl1 == ANODES["Cu"][0]
    head = tmp_path / "head.xy"
    head.write_text("# ANODE = Co\n# WLRATIO = 0\n# RADIUS = 300\n" + data)
    p = read_pattern(str(head))
    assert p.assumed == [] and p.wl1 == ANODES["Co"][0] and p.ka2_stripped and p.radius_mm == 300
    assert read_pattern(os.path.join(ROOT, "examples", "synthetic_Ti64_A.xy")).assumed == []


def test_radiation_and_radius_overrides(tmp_path):
    plain = tmp_path / "plain.xy"
    plain.write_text("\n".join(f"{30 + 0.02 * i:.2f} {100 + i}" for i in range(50)))
    p = read_pattern(str(plain), radiation="Mo", radius_mm=185, ka2_stripped=True)
    assert p.wl1 == ANODES["Mo"][0] and p.anode == "Mo" and p.radius_mm == 185 and p.ka2_ratio == 0
    assert p.assumed == []
    q = read_pattern(str(plain), radiation=(1.5, 1.51, 0.48))
    assert (q.wl1, q.wl2, q.ka2_ratio) == (1.5, 1.51, 0.48)


# ---------------------------------------------------------------- standards
def test_standard_reflection_lists():
    lab = [r[1] for r in standards.reflections("corundum", 1.540598, tt_max=70)]
    assert lab[:6] == ["012", "104", "110", "006", "113", "202"] and "300" in lab
    assert [r[1] for r in standards.reflections("Si", 1.540598, tt_max=80)] == ["111", "220", "311", "400", "331"]
    assert [r[1] for r in standards.reflections("LaB6", 1.540598, tt_max=40)] == ["100", "110", "111"]
    assert [r[1] for r in standards.reflections("CeO2", 1.540598, tt_max=50)] == ["111", "200", "220"]
    si = standards.reflections("Si", 1.540598, tt_max=30)[0][0]
    assert si == pytest.approx(28.442, abs=0.003)          # Si 111 with Cu Ka1


def test_zero_shift_and_displacement_are_recovered():
    wl, R, z, s = 1.540598, 250.0, 0.035, 60.0
    calc = np.array([r[0] for r in standards.reflections("LaB6", wl, tt_max=140)])
    th = np.deg2rad(calc / 2)
    obs = calc + z - np.rad2deg(2 * s * 1e-3 * np.cos(th) / R)
    lab, c = standards.index_peaks(obs, "LaB6", wl)
    assert all(lab)
    zs = standards.zero_shift(obs, c, R)
    assert zs["zero_deg"] == pytest.approx(z, abs=1e-6) and zs["disp_um"] == pytest.approx(s, abs=1e-3)


def test_wrong_standard_is_detected():
    wl = 1.540598
    obs = [r[0] for r in standards.reflections("corundum", wl, tt_max=100)][:15]
    lab, _ = standards.index_peaks(obs, "Si", wl)
    assert sum(l is not None for l in lab) <= 2


def test_instrument_from_lab6_with_impurity_and_cobalt():
    wl1, wl2 = ANODES["Co"]
    z = 0.02
    peaks = [(t + z, 2000.0) for t, _, _ in standards.reflections("LaB6", wl1, tt_max=118)]
    peaks.append((47.0, 1500.0))                                  # not a LaB6 line
    pat = _pattern(peaks, wl1, wl2, x0=20, x1=120, step=0.01)
    inst = fit_instrument(pat, standard="LaB6")
    assert inst.standard == "LaB6" and inst.wavelength[0] == wl1
    assert inst.zero_shift_deg == pytest.approx(z, abs=0.004)
    assert 47.0 not in [round(t, 1) for t in inst.points["two_theta"]]
    assert any(m.key == "w.std_unindexed" for m in inst.fit_warnings)
    # the same pattern read as Cu (wrong radiation): few peaks match LaB6
    pat_cu = Pattern(pat.two_theta, pat.counts, *ANODES["Cu"], 0.5, "x", {}, 250.0)
    bad = fit_instrument(pat_cu, standard="LaB6")
    assert any(m.key == "w.std_mismatch" for m in bad.fit_warnings)


def test_old_instrument_files_still_load(tmp_path):
    d = {"gauss_coef": [0.0, 0.003], "lorentz_coef": [0.0, 0.001], "k_range": [3, 9], "name": "old",
         "points": {}, "_generator": "x", "future_field": 1}
    f = tmp_path / "old.json"
    f.write_text(json.dumps(d))
    inst = InstrumentModel.load(str(f))
    assert inst.standard == "" and inst.zero_shift_deg == 0.0 and inst.describe() == []
    ex = InstrumentModel.load(os.path.join(ROOT, "autodisloc", "data", "instrument_corundum_example.json"))
    assert ex.standard == "corundum" and ex.n_indexed == ex.n_found == 18


# ---------------------------------------------------------- materials, other wavelengths
def _ti_pattern(a, c, wl1, wl2, ratio=0.5, x1=120.0):
    peaks = []
    for lab, h, k, l in ti64.ALPHA_REFLECTIONS:
        t = ti64.two_theta(ti64.d_hcp(h, k, l, a, c), wl1)
        if 25 < t < x1 - 1:
            peaks.append((t, 30.0 * ti64.ICDD_ALPHA_INTENSITY[lab]))
    return _pattern(peaks, wl1, wl2, ratio, x0=25, x1=x1, step=0.02, w=0.15)


@pytest.mark.parametrize("anode", ["Cu", "Co"])
def test_cp_ti_with_ti64_preset_and_other_wavelength(anode):
    a, c = 2.9505, 4.6826                                   # CP-Ti, about 1 % larger than the Ti64 preset
    wl1, wl2 = ANODES[anode]
    pat = _ti_pattern(a, c, wl1, wl2)
    opts = AnalysisOptions(whole_profile=False, mc_draws=0, beta="no")
    na, nc, _ = nominal_lattice(pat, opts)
    assert na == pytest.approx(a, abs=0.004) and nc == pytest.approx(c, abs=0.006)
    fits = [f for f in fit_alpha_peaks(pat, opts, (na, nc, 3.3)) if f.label in opts.reflections]
    lat = phase_lattice(fits, [], pat)
    assert lat["a"] == pytest.approx(a, abs=5e-4) and lat["c"] == pytest.approx(c, abs=8e-4)


def test_zero_shift_correction_of_lattice_parameters():
    a, c, z = 2.93, 4.675, 0.05
    wl = ANODES["Cu"][0]
    from autodisloc.peaks import PeakFit
    fits = [PeakFit(lab, ti64.two_theta(ti64.d_hcp(h, k, l, a, c), wl) + z, 1.0, 0.1, 0.1)
            for lab, h, k, l in ti64.ALPHA_REFLECTIONS]
    pat = Pattern(np.array([20.0, 90.0]), np.zeros(2), wl, ANODES["Cu"][1], 0.5, "", {}, 250.0)
    fixed = phase_lattice(fits, [], pat, zero_shift_deg=z)
    assert fixed["a"] == pytest.approx(a, abs=1e-6) and fixed["c"] == pytest.approx(c, abs=1e-6)
    assert abs(fixed["disp_um"]) < 1e-3


def test_material_presets():
    assert set(materials.MATERIAL_KEYS) >= {"Ti-6Al-4V", "CP-Ti", "custom"}
    assert materials.get("Ti-6Al-4V").a == ti64.ALPHA_A and materials.get("CP-Ti").beta == "no"
    assert materials.get("unknown").key == "Ti-6Al-4V"


def test_anode_is_suggested_for_files_without_wavelength(tmp_path):
    from autodisloc.pipeline import measurement_warnings
    wl1, wl2 = ANODES["Co"]
    pat = _ti_pattern(2.925, 4.670, wl1, wl2)
    f = tmp_path / "co_without_header.xy"
    f.write_text("\n".join(f"{x:.3f} {y:.0f}" for x, y in zip(pat.two_theta, pat.counts)))
    p = read_pattern(str(f))
    assert "wavelength" in p.assumed and p.anode == "Cu"
    keys = [m.key for m in measurement_warnings(p, None)]
    assert "w.wl_assumed" in keys and "w.wl_guess" in keys
    assert ti64.best_anode(p)[0] == "Co"
    cu = read_pattern(os.path.join(ROOT, "examples", "synthetic_Ti64_A.xy"), radiation="Cu")
    assert ti64.best_anode(cu)[0] == "Cu"


def test_other_diffractometer_is_detected_from_the_radius(tmp_path):
    from autodisloc.pipeline import measurement_warnings
    inst = InstrumentModel.load(os.path.join(ROOT, "autodisloc", "data", "instrument_corundum_example.json"))
    f = tmp_path / "panalytical.xrdml"
    f.write_text(XRDML.replace("1.7890100", "1.5405980").replace("1.7928500", "1.5444260"), encoding="utf-8")
    keys = [m.key for m in measurement_warnings(read_pattern(str(f)), inst)]       # 240 mm vs 250 mm
    assert keys == ["w.radius_mismatch"]
    same = read_pattern(os.path.join(ROOT, "examples", "synthetic_Ti64_A.xy"))      # header: 250 mm
    assert measurement_warnings(same, inst) == []
