# SPDX-License-Identifier: MIT
# AutoDisloc 2 - Copyright (c) 2026 Firat Memu
"""Harris texture coefficients from integrated intensities.

T_hkl = (I/I0)_hkl / mean_hkl(I/I0); T = 1 for a random powder. The mean
contrast factors of Dragomir & Ungar assume an untextured polycrystal, so
strongly textured reflections are flagged.
"""

import numpy as np

from .ti64 import ICDD_ALPHA_INTENSITY


def harris(labels, areas, reference=ICDD_ALPHA_INTENSITY, low=0.5, high=2.0):
    ratio = np.array([a / reference[l] for l, a in zip(labels, areas)], float)
    T = ratio / ratio.mean()
    flagged = [l for l, t in zip(labels, T) if t < low or t > high]
    return dict(zip(labels, T)), flagged
