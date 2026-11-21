# SPDX-License-Identifier: MIT
# AutoDisloc 2 - Copyright (c) 2026 Firat Memu
"""Texts in both languages; profile-likelihood interval interpolation."""
import os
import string
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from autodisloc.i18n import STRINGS, Msg, set_language, tr
from autodisloc.pipeline import SUMMARY_KEYS
from autodisloc.wholeprofile import interval_from_profile


def _fields(s):
    return {f for _, f, _, _ in string.Formatter().parse(s) if f}


def test_every_text_has_both_languages_with_the_same_fields():
    for key, (t, e) in STRINGS.items():
        assert t and e, key
        assert _fields(t) == _fields(e), key


def test_every_summary_column_has_a_label():
    for k in SUMMARY_KEYS:
        assert "col." + k in STRINGS


def test_messages_follow_the_active_language():
    m = Msg("w.mwh_poor", r2=0.5)
    set_language("en")
    assert "Poor mWH fit" in str(m)
    set_language("tr")
    assert "mWH uyumu zayıf" in str(m)
    assert tr("yes") == "EVET"
    set_language("en")


def test_profile_interval_is_interpolated_and_includes_the_best_fit():
    # chi2 parabola in log rho with minimum at 11 (below the scan start)
    dof, c0 = 1000, 1000.0
    g = np.r_[11.0, np.arange(11.0, 16.01, 0.125)]
    chi2 = c0 + 3.84 * (g - 11.0) ** 2 / 0.25        # crosses the threshold at 11.5
    lo, hi = interval_from_profile(g, chi2, c0, dof)
    assert lo is None
    assert abs(np.log10(hi) - 11.5) < 0.03


def test_lattice_cohen_with_displacement_regression():
    """Cohen's method with the sin(theta)cos^2(theta) drift term on a fixed set
    of measured Ti-6Al-4V peak positions; reference values from an independent
    implementation of the same method (a = 2.933, c = 4.676 Angstrom)."""
    from autodisloc.ti64 import fit_hcp_lattice_displacement
    tt = [35.39, 38.554, 40.431, 53.274, 63.429, 70.929, 76.693, 77.924]
    hkl = [(1, 0, 0), (0, 0, 2), (1, 0, 1), (1, 0, 2), (1, 1, 0), (1, 0, 3), (1, 1, 2), (2, 0, 1)]
    r = fit_hcp_lattice_displacement(tt, hkl, 1.5404)
    assert abs(r["a"] - 2.9332) < 2e-4 and abs(r["c"] - 4.6760) < 2e-4


def test_displacement_is_recovered():
    import numpy as np
    from autodisloc.ti64 import d_hcp, displacement_correct, fit_hcp_lattice_displacement, two_theta
    hkl = [(1, 0, 0), (0, 0, 2), (1, 0, 1), (1, 0, 2), (1, 1, 0), (1, 0, 3), (1, 1, 2), (2, 0, 1)]
    tt = np.array([two_theta(d_hcp(h, k, l, 2.925, 4.670), 1.540598) for h, k, l in hkl])
    shifted = 2 * tt - displacement_correct(tt, 120.0)          # specimen 120 um displaced
    r = fit_hcp_lattice_displacement(shifted, hkl, 1.540598)
    assert abs(r["a"] - 2.925) < 1e-4 and abs(r["c"] - 4.670) < 1e-4 and abs(r["disp_um"] - 120) < 3
