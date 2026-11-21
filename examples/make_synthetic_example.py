# SPDX-License-Identifier: MIT
# AutoDisloc 2 - Copyright (c) 2026 Firat Memu
"""Synthetic Ti-6Al-4V example patterns with known microstructure.

    python examples/make_synthetic_example.py

writes examples/synthetic_Ti64_A.xy (rho = 1.0e15 m^-2) and
examples/synthetic_Ti64_B.xy (rho = 1.0e11 m^-2, below the detection limit)
generated with the Wilkens whole-profile model, the example instrument model
(Cu Ka1 + Ka2) and Poisson counting noise. The true parameters are written
in the file header. The whitepaper uses them as the worked example.
"""

import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

from autodisloc import InstrumentModel, ti64  # noqa: E402
from autodisloc.io import Pattern  # noqa: E402
from autodisloc.mwa import ETA_FACTOR  # noqa: E402
from autodisloc.wholeprofile import _Model  # noqa: E402

INST = os.path.join(os.path.dirname(HERE), "autodisloc", "data", "instrument_corundum_example.json")

# name: rho (m^-2), M*, u (Burgers-type softmax parameters), size median m (nm), sigma, peak scale, seed
EXAMPLES = {
    "A": (1.0e15, 1.3, (-2.5, -2.6), 90.0, 0.30, 6000.0, 11),
    "B": (1.0e11, 1.3, (-2.5, -2.6), 300.0, 0.25, 6000.0, 12),
}


def synthesize(rho, M_star, u, m, sigma, scale, seed, inst):
    x = np.round(np.arange(25.0, 90.0001, 0.02), 4)
    pat = Pattern(two_theta=x, counts=np.zeros_like(x), wl1=1.540598, wl2=1.544426,
                  ka2_ratio=0.5, source="synthetic")
    mdl = _Model(pat, inst, None, ti64.ALPHA_A / 10, ("S3",), 1.0)
    h, b2c, q1, q2 = mdl.population(*u)
    rho_nm = rho * 1e-18
    Re = M_star / np.sqrt(rho_nm) * ETA_FACTOR          # mWA convention
    y = 150.0 + 0.4 * (x - 55.0)
    for lab, hh, kk, ll in ti64.ALPHA_REFLECTIONS + ti64.ALPHA_NUISANCE:
        c = ti64.two_theta(ti64.d_hcp(hh, kk, ll, ti64.ALPHA_A, ti64.ALPHA_C), 1.540598)
        if not (x[0] + 1 < c < x[-1] - 1):
            continue
        rel = ti64.ICDD_ALPHA_INTENSITY.get(lab, 4)
        y = y + mdl.peak(x, c, scale * rel / 100, ll, (rho_nm, Re, m, sigma, h, b2c, q1, q2))
    counts = np.random.default_rng(seed).poisson(np.maximum(y, 0)).astype(float)
    truth = {"rho_m-2": rho, "M_star": M_star, "Re_star_nm": M_star / np.sqrt(rho_nm),
             "h_a": h[0], "h_c": h[1], "h_c+a": h[2], "b2C_hk0_nm2": b2c, "q1": q1, "q2": q2,
             "size_median_nm": m, "size_sigma": sigma}
    return x, counts, truth


def main():
    inst = InstrumentModel.load(INST)
    for name, args in EXAMPLES.items():
        x, counts, truth = synthesize(*args, inst)
        path = os.path.join(HERE, f"synthetic_Ti64_{name}.xy")
        with open(path, "w", encoding="utf-8") as f:
            f.write("# AutoDisloc synthetic Ti-6Al-4V pattern, Cu Ka1+Ka2 (ratio 0.5), Poisson noise\n")
            # measurement data read by autodisloc.io (wavelengths in Angstrom, radius in mm)
            f.write("# WL1 = 1.540598\n# WL2 = 1.544426\n# WLRATIO = 0.5\n# RADIUS = 250\n")
            f.write("# instrument: autodisloc/data/instrument_corundum_example.json\n")
            for k, v in truth.items():
                f.write(f"# true {k} = {v:.6g}\n")
            f.write("# 2theta_deg counts\n")
            for a, b in zip(x, counts):
                f.write(f"{a:.4f} {b:.0f}\n")
        print(path, {k: round(v, 4) if v < 1e6 else f"{v:.2e}" for k, v in truth.items()})


if __name__ == "__main__":
    main()
