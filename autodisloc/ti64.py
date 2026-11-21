# SPDX-License-Identifier: MIT
# AutoDisloc 2 - Copyright (c) 2026 Firat Memu
"""Crystallographic data for Ti-6Al-4V phases and small helpers."""

import numpy as np

# Nominal lattice parameters used only to predict peak positions (Angstrom)
ALPHA_A, ALPHA_C = 2.925, 4.670
BETA_A = 3.205

# alpha/alpha' reflections used in line-profile analysis: (label, h, k, l)
ALPHA_REFLECTIONS = [
    ("10.0", 1, 0, 0),
    ("00.2", 0, 0, 2),
    ("10.1", 1, 0, 1),
    ("10.2", 1, 0, 2),
    ("11.0", 1, 1, 0),
    ("10.3", 1, 0, 3),
    ("11.2", 1, 1, 2),
    ("20.1", 2, 0, 1),
]
# weak alpha reflections that must be modelled when they fall inside a window
# but are not used in the analysis
ALPHA_NUISANCE = [("20.0", 2, 0, 0), ("20.2", 2, 0, 2)]

BETA_REFLECTIONS = [("b110", 1, 1, 0), ("b200", 2, 0, 0), ("b211", 2, 1, 1)]

# Relative intensities of untextured alpha-Ti, ICDD PDF 44-1294 (Cu Ka).
# Used only for the Harris texture coefficient; verify against the card.
ICDD_ALPHA_INTENSITY = {
    "10.0": 25, "00.2": 30, "10.1": 100, "10.2": 13,
    "11.0": 11, "10.3": 11, "11.2": 9, "20.1": 6,
}


def d_hcp(h, k, l, a, c):
    return 1.0 / np.sqrt(4.0 / 3.0 * (h * h + h * k + k * k) / a ** 2 + l * l / c ** 2)


def d_cubic(h, k, l, a):
    return a / np.sqrt(h * h + k * k + l * l)


def two_theta(d, wl):
    s = wl / (2.0 * d)
    return 2.0 * np.rad2deg(np.arcsin(np.clip(s, -1, 1)))


def expected_positions(wl, a=ALPHA_A, c=ALPHA_C, a_beta=BETA_A, with_beta=True):
    """Return [(2theta, key)] for alpha, nuisance alpha and (optionally) beta."""
    out = [(two_theta(d_hcp(h, k, l, a, c), wl), lab) for lab, h, k, l in ALPHA_REFLECTIONS]
    out += [(two_theta(d_hcp(h, k, l, a, c), wl), "n" + lab) for lab, h, k, l in ALPHA_NUISANCE]
    if with_beta:
        out += [(two_theta(d_cubic(h, k, l, a_beta), wl), lab) for lab, h, k, l in BETA_REFLECTIONS]
    return out


def hkl_of(label):
    for lab, h, k, l in ALPHA_REFLECTIONS:
        if lab == label:
            return h, k, l
    raise KeyError(label)


def fit_hcp_lattice(two_thetas, hkls, wl):
    """Least-squares a, c (Angstrom) from sin^2(theta) = C(h^2+hk+k^2) + B l^2."""
    th = np.deg2rad(np.asarray(two_thetas) / 2.0)
    A = np.array([[h * h + h * k + k * k, l * l] for h, k, l in hkls], float)
    sol, *_ = np.linalg.lstsq(A, np.sin(th) ** 2, rcond=None)
    C, B = sol
    return wl / np.sqrt(3.0 * C), wl / np.sqrt(4.0 * B)


def fit_hcp_lattice_displacement(two_thetas, hkls, wl, radius_mm=250.0):
    """Lattice parameters a, c (Angstrom) with Cohen's least squares including the
    specimen-displacement term of Bragg-Brentano geometry.

    A displacement s of the specimen surface shifts a reflection by
    d(2theta) = -2 s cos(theta) / R, i.e. d(sin^2 theta) = -(2 s / R) sin(theta) cos^2(theta).
    The model sin^2 theta = C (h^2+hk+k^2) + B l^2 + D sin(theta) cos^2(theta)
    is linear in (C, B, D); a = wl / sqrt(3C), c = wl / sqrt(4B), s = -D R / 2.
    Standard errors follow from the residual variance (n - 3 degrees of freedom)."""
    th = np.deg2rad(np.asarray(two_thetas, float) / 2.0)
    A = np.array([[h * h + h * k + k * k, l * l, np.sin(t) * np.cos(t) ** 2] for (h, k, l), t in zip(hkls, th)],
                 float)
    y = np.sin(th) ** 2
    sol, *_ = np.linalg.lstsq(A, y, rcond=None)
    C, B, D = sol
    dof = len(y) - 3
    if dof > 0:
        s2 = float(np.sum((y - A @ sol) ** 2) / dof)
        cov = s2 * np.linalg.pinv(A.T @ A)
        eC, eB, eD = np.sqrt(np.clip(np.diag(cov), 0, None))
    else:
        eC = eB = eD = np.nan
    a, c = wl / np.sqrt(3.0 * C), wl / np.sqrt(4.0 * B)
    a_err, c_err = a * eC / (2 * C), c * eB / (2 * B)
    disp_um = -D * radius_mm / 2.0 * 1000.0
    return {"a": float(a), "a_err": float(a_err), "c": float(c), "c_err": float(c_err),
            "ca": float(c / a), "ca_err": float(c / a * np.hypot(a_err / a, c_err / c)),
            "disp_um": float(disp_um), "disp_err_um": float(eD * radius_mm / 2.0 * 1000.0), "n": len(y)}


def displacement_correct(two_theta_deg, disp_um, radius_mm=250.0):
    """Peak position corrected for a specimen displacement (inverse of the shift above)."""
    th = np.deg2rad(np.asarray(two_theta_deg, float) / 2.0)
    return np.asarray(two_theta_deg, float) + np.rad2deg(2 * disp_um * 1e-3 * np.cos(th) / radius_mm)


BETA_HKL = {"b110": (1, 1, 0), "b200": (2, 0, 0), "b211": (2, 1, 1)}


def beta_lattice(beta_peaks, wl, disp_um, radius_mm=250.0):
    """Cubic beta lattice parameter (Angstrom) from the fitted beta reflections,
    displacement-corrected; mean over reflections with its standard error."""
    vals, errs = [], []
    for lab, tt, ett in beta_peaks:
        h, k, l = BETA_HKL[lab]
        t = displacement_correct(tt, disp_um, radius_mm)
        th = np.deg2rad(t / 2.0)
        a = wl * np.sqrt(h * h + k * k + l * l) / (2.0 * np.sin(th))
        vals.append(a)
        errs.append(a / np.tan(th) * np.deg2rad(ett / 2.0) if np.isfinite(ett) else np.nan)
    if not vals:
        return np.nan, np.nan, 0
    vals = np.array(vals)
    if len(vals) > 1:
        return float(vals.mean()), float(vals.std(ddof=1) / np.sqrt(len(vals))), len(vals)
    return float(vals[0]), float(errs[0]), 1


def refine_nominal(pattern, a=ALPHA_A, c=ALPHA_C, max_dev=0.035):
    """Nominal alpha lattice adjusted to the measured pattern.

    Only used to place the fit windows and start values, so that alloys,
    wavelengths and goniometer offsets other than those of the presets work.
    A coarse isotropic scale search matches the predicted alpha reflections
    to the strongest observed maxima; a, c then follow from a least-squares
    fit of the matched positions. Returns (a, c, n_matched); the input values
    are returned unchanged when fewer than four reflections match."""
    from scipy.signal import find_peaks
    x, y = np.asarray(pattern.two_theta, float), np.asarray(pattern.counts, float)
    wl = pattern.wl1
    if len(x) < 20:
        return a, c, 0
    step = float(np.median(np.diff(x)))
    idx, prop = find_peaks(y, prominence=0.03 * float(np.ptp(y)), distance=max(int(0.25 / step), 1))
    if len(idx) < 3:
        return a, c, 0
    obs, w = x[idx], prop["prominences"]

    def predicted(s, cs=1.0):
        out = []
        for lab, h, k, l in ALPHA_REFLECTIONS:
            t = two_theta(d_hcp(h, k, l, a * s, c * s * cs), wl)
            if x.min() + 0.3 < t < x.max() - 0.3:
                out.append((t, (h, k, l)))
        return out

    best = (-1.0, 1.0, 1.0)
    for cs in np.arange(0.98, 1.02 + 1e-9, 0.001):
        for s in np.arange(1 - max_dev, 1 + max_dev + 1e-9, 0.0005):
            score = 0.0
            for t, _ in predicted(s, cs):
                dist = np.abs(obs - t)
                j = int(np.argmin(dist))
                if dist[j] < 0.06:
                    score += w[j]
            dev = abs(s - 1) + abs(cs - 1)
            if score > best[0] + 1e-9 or (abs(score - best[0]) <= 1e-9 and dev < abs(best[1] - 1) + abs(best[2] - 1)):
                best = (score, s, cs)
    _, s, cs = best
    pairs, used = [], set()
    for t, hkl in predicted(s, cs):
        dist = np.abs(obs - t)
        j = int(np.argmin(dist))
        if dist[j] < 0.08 and j not in used:
            used.add(j)
            pairs.append((obs[j], hkl))
    has_l = any(h[2] for _, h in pairs)
    has_hk = any(h[0] or h[1] for _, h in pairs)
    if len(pairs) < 4 or not (has_l and has_hk):
        return a, c, len(pairs)
    a1, c1 = fit_hcp_lattice([p[0] for p in pairs], [p[1] for p in pairs], wl)
    if abs(a1 / a - 1) > max_dev or abs(c1 / c - 1) > max_dev:
        return a, c, len(pairs)
    return float(a1), float(c1), len(pairs)


def best_anode(pattern, a=ALPHA_A, c=ALPHA_C):
    """Anode whose Ka1 wavelength indexes the alpha-Ti peaks of the pattern best.

    Used only when a file contains no wavelength: the anodes differ by more
    than the +-3.5 % lattice search of refine_nominal, so only the right one
    matches many reflections. Returns (anode, n_matched) or ("", 0)."""
    from dataclasses import replace
    from .io import ANODES
    best = ("", 0)
    for name, (w1, w2) in ANODES.items():
        _, _, n = refine_nominal(replace(pattern, wl1=w1, wl2=w2), a, c)
        if n > best[1]:
            best = (name, n)
    return best


def to_k(two_theta_deg, width_deg, wl_nm):
    """K = 2 sin(theta)/lambda and Delta K = cos(theta) Delta(2theta)/lambda, nm^-1."""
    th = np.deg2rad(np.asarray(two_theta_deg) / 2.0)
    K = 2.0 * np.sin(th) / wl_nm
    dK = np.cos(th) * np.deg2rad(np.asarray(width_deg)) / wl_nm
    return K, dK
