# SPDX-License-Identifier: MIT
# AutoDisloc 2 - Copyright (c) 2026 Firat Memu
"""Full analysis: Voigt peak fitting -> instrument correction -> mWH ->
Burgers-vector population -> mWA -> Wilkens whole-profile fit -> validity
checks and uncertainty. See the whitepaper in docs/whitepaper/."""

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from . import ti64
from .i18n import Msg
from .contrast import combinations_summary, contrast_hkl, solve_population
from .instrument import correct
from .mwa import l_range_sensitivity, run_mwa
from .mwh import fit_mwh, fit_mwh_population
from .peaks import MERGE_GAP, fit_group, make_windows, voigt_fwhm
from .texture import harris


@dataclass
class AnalysisOptions:
    fourier_mode: str = "voigt"          # "voigt" (Voigt transform) or "eq13" (Muiruri 2020 Eq. 13)
    contrast_method: str = "type_average"  # or "subsystems"
    exclude_subsystems: tuple = ("S3",)
    a_min: float = 0.1                   # minimum A(L) kept in the L grid
    limit_L_to_Re: bool = True
    beta: str = "auto"                   # "auto", "yes", "no"
    reflections: tuple = tuple(r[0] for r in ti64.ALPHA_REFLECTIONS)
    mc_draws: int = 200
    seed: int = 1
    # "constrained": mWH written with the Burgers-type fractions (q always
    # attainable, h always proper fractions); "free": q1, q2 fitted freely
    mwh_mode: str = "constrained"
    whole_profile: bool = True           # Wilkens whole-profile fit (main result)
    wp_starts: tuple = (14.0, 15.0, 16.0)
    # when the free fit cannot separate rho from the arrangement parameter
    # (M* or rho at a bound), M* is fixed: reference value and band. 2.64 is
    # only the geometric mean of the free-fit M* (2.17 and 3.21) of two
    # well-conditioned samples measured during the development of the program
    # with the example instrument model, not a universal constant; users should
    # set a value for their material and instrument (warning w.wp_fixed_ref).
    # M* is the program's convention (wholeprofile.py): M* = 2 e^(1/4) x the
    # M* of Ribarik et al. 2001 (MWP-fit/CMWP)
    wp_M_ref: float = 2.64
    wp_M_band: tuple = (1.5, 4.0)
    # material: nominal alpha a, c and beta a (Angstrom) place the fit windows;
    # refine_nominal adjusts them to the measured pattern when they are far off
    # (see REFINE_IF_OFF_DEG)
    material: str = "Ti-6Al-4V"
    nominal_lattice: tuple = (ti64.ALPHA_A, ti64.ALPHA_C, ti64.BETA_A)
    refine_nominal: bool = True
    # subtract the goniometer zero shift of the instrument standard from the
    # sample peak positions before the lattice-parameter fit (meaningful with
    # a standard of certified lattice parameter)
    apply_zero_shift: bool = False


@dataclass
class AnalysisResult:
    sample: str
    peaks: pd.DataFrame
    lattice_a_A: float
    lattice_c_A: float
    mwh: object
    population: object
    mwa: object
    texture: dict
    warnings: list
    valid: bool
    mc: dict = field(default_factory=dict)
    l_sensitivity: dict = field(default_factory=dict)
    options: AnalysisOptions = None
    beta_peaks: pd.DataFrame = None
    mwh_free: object = None              # free q1, q2 fit
    combos: dict = None                  # 40-combination h on the free q (one sub-system per type)
    wp: object = None                    # WholeProfileResult
    wp_interval: tuple = (np.nan, np.nan)
    wp_interval_method: str = ""
    pattern: object = None               # the measured pattern (for figures)
    lattice: dict = field(default_factory=dict)   # displacement-corrected a, c, c/a, a_beta
    nominal: tuple = None                # (a, c, a_beta) used to place the fit windows
    alpha_fits: list = None              # Voigt PeakFit objects of the analysed peaks

    def summary(self):
        """One row per sample with stable keys (see SUMMARY_KEYS). The first
        block is the final result (whole-profile Wilkens fit); the rest
        documents the Voigt-mWA chain. Text values may be Msg objects; use
        report.summary_frame() for a localised table."""
        p, m, w = self.population, self.mwa, self.mwh
        wp = self.wp
        nan = np.nan
        d = {"sample": self.sample}
        upper_only = wp is not None and wp.rho < 2e13
        if wp is None:
            text = "-"
        elif upper_only:
            text = f"< {self.wp_interval[1]:.2e}"
        else:
            text = f"{wp.rho:.2e} ({self.wp_interval[0]:.1e} - {self.wp_interval[1]:.1e})"
        d.update({
            "rho": nan if (wp is None or upper_only) else wp.rho,
            "rho_text": text,
            "rho_lo": self.wp_interval[0],
            "rho_hi": self.wp_interval[1],
            "interval_method": self.wp_interval_method,
            "M_star": wp.M_star if wp is not None else nan,
            "Re_star_nm": wp.Re_star_nm if wp is not None else nan,
            "h_a": wp.h["a"] if wp is not None else nan,
            "h_c": wp.h["c"] if wp is not None else nan,
            "h_ca": wp.h["c+a"] if wp is not None else nan,
            "b2c_hk0": wp.b2c_hk0 if wp is not None else nan,
            "size_m_nm": wp.m_nm if wp is not None else nan,
            "size_sigma": wp.sigma if wp is not None else nan,
            "rwp": wp.rwp if wp is not None else nan,
            "chi2_dof": wp.params["chi2"] / wp.params["dof"] if wp is not None else nan,
        })
        sens = [v[0] for v in self.l_sensitivity.values()] if self.l_sensitivity else []
        d.update({
            "mwa_rho": m.rho if self.valid else nan,
            "mwa_valid": Msg("yes") if self.valid else Msg("no"),
            "mwa_p16": self.mc.get("p16", nan), "mwa_p84": self.mc.get("p84", nan),
            "mwa_Lmin": np.nanmin(sens) if sens and np.isfinite(sens).any() else nan,
            "mwa_Lmax": np.nanmax(sens) if sens and np.isfinite(sens).any() else nan,
            "mwa_Re_nm": m.Re_nm, "mwa_M": m.M, "mwa_r2": m.r2,
            "mwa_L": f"{m.L.min():.0f}-{m.L.max():.0f}",
            "mwh_mode": self.options.mwh_mode if self.options else "",
            "mwh_q1": w.q1, "mwh_q2": w.q2, "mwh_r2": w.r2, "mwh_D_nm": w.D_nm,
            "mwh_h_a": p.h["a"], "mwh_h_c": p.h["c"], "mwh_h_ca": p.h["c+a"],
            "mwh_b2c": p.b2c_hk0, "mwh_b2c_min": p.b2c_min, "mwh_b2c_max": p.b2c_max,
        })
        f = self.mwh_free
        c = self.combos
        d.update({
            "free_q1": f.q1 if f is not None else nan,
            "free_q2": f.q2 if f is not None else nan,
            "comb_n": c["n"] if c else 0,
            "comb_h_a": c["mean"]["h_a"] if c else nan,
            "comb_h_c": c["mean"]["h_c"] if c else nan,
            "comb_h_ca": c["mean"]["h_c+a"] if c else nan,
            "comb_b2c": c["mean"]["b2C_hk0"] if c else nan,
            "a_A": self.lattice.get("a", self.lattice_a_A), "a_err": self.lattice.get("a_err", nan),
            "c_A": self.lattice.get("c", self.lattice_c_A), "c_err": self.lattice.get("c_err", nan),
            "ca": self.lattice.get("ca", self.lattice_c_A / self.lattice_a_A),
            "a_beta_A": self.lattice.get("a_beta", nan), "a_beta_err": self.lattice.get("a_beta_err", nan),
            "disp_um": self.lattice.get("disp_um", nan),
            "fourier_mode": self.options.fourier_mode if self.options else "",
            "ka2": (Msg("ka2.stripped") if self.pattern is not None and self.pattern.ka2_stripped
                    else Msg("ka2.present")) if self.pattern is not None else "",
        })
        return d

    @property
    def upper_limit_only(self):
        return self.wp is not None and self.wp.rho < 2e13


# Column order of the summary table; labels are i18n keys "col.<key>"
SUMMARY_KEYS = [
    "sample", "rho", "rho_text", "rho_lo", "rho_hi", "interval_method", "M_star", "Re_star_nm",
    "h_a", "h_c", "h_ca", "b2c_hk0", "size_m_nm", "size_sigma", "rwp", "chi2_dof",
    "mwa_rho", "mwa_valid", "mwa_p16", "mwa_p84", "mwa_Lmin", "mwa_Lmax", "mwa_Re_nm", "mwa_M",
    "mwa_r2", "mwa_L", "mwh_mode", "mwh_q1", "mwh_q2", "mwh_r2", "mwh_D_nm", "mwh_h_a", "mwh_h_c",
    "mwh_h_ca", "mwh_b2c", "mwh_b2c_min", "mwh_b2c_max", "free_q1", "free_q2", "comb_n",
    "comb_h_a", "comb_h_c", "comb_h_ca", "comb_b2c", "a_A", "a_err", "c_A", "c_err", "ca", "a_beta_A",
    "a_beta_err", "disp_um", "fourier_mode", "ka2",
]


# The nominal lattice is replaced by the refined one only when it would place
# an alpha reflection further from the measured peak than the centre bound of
# the Voigt fits (0.35 deg): a wrong preset (CP-Ti data with the Ti-6Al-4V
# values: 0.6-1.0 deg), another alloy or a large goniometer offset. With the
# right preset the difference is below 0.3 deg and the windows stay as they are,
# so established results do not change.
REFINE_IF_OFF_DEG = 0.35


def nominal_lattice(pattern, opts):
    """(a, c, a_beta) used to place the fit windows."""
    a, c, ab = opts.nominal_lattice
    if opts.refine_nominal:
        a1, c1, n = ti64.refine_nominal(pattern, a, c)
        x = pattern.two_theta
        off = [abs(ti64.two_theta(ti64.d_hcp(h, k, l, a1, c1), pattern.wl1)
                   - ti64.two_theta(ti64.d_hcp(h, k, l, a, c), pattern.wl1))
               for _, h, k, l in ti64.ALPHA_REFLECTIONS
               if x.min() < ti64.two_theta(ti64.d_hcp(h, k, l, a, c), pattern.wl1) < x.max()]
        if n >= 4 and off and max(off) > REFINE_IF_OFF_DEG:
            a, c = a1, c1
    return (a, c, ab)


def fit_alpha_peaks(pattern, opts, nominal=None):
    """Fit all alpha (and nuisance/beta) peaks of a titanium pattern."""
    x, y = pattern.two_theta, pattern.counts
    wl = pattern.wl1
    with_beta = opts.beta != "no"
    nominal = nominal or tuple(opts.nominal_lattice)
    pos = [(t, k) for t, k in ti64.expected_positions(wl, *nominal, with_beta=with_beta)
           if x.min() + 0.5 < t < x.max() - 0.5]
    wins = make_windows(pos, x.min(), x.max(), half_width=1.0, merge_gap=MERGE_GAP)
    fits = []
    for gid, (a, b, group) in enumerate(wins):
        if not any(k in opts.reflections for _, k in group):
            continue
        m = (x >= a) & (x <= b)
        res = fit_group(x[m], y[m], [g[0] for g in group], pattern.ka2_ratio,
                        pattern.wl1, pattern.wl2, 0.35, [g[1] for g in group], gid)
        betas = [f for f in res if f.label.startswith("b")]
        if betas and opts.beta == "auto":
            weak = all(f.area < 3 * (f.area_err if np.isfinite(f.area_err) else np.inf)
                       or f.at_bound for f in betas)
            if weak:
                g2 = [g for g in group if not g[1].startswith("b")]
                res = fit_group(x[m], y[m], [g[0] for g in g2], pattern.ka2_ratio,
                                pattern.wl1, pattern.wl2, 0.35, [g[1] for g in g2], gid)
        fits += res
    return fits


def analyze(pattern, instrument, sample_name=None, options=None, **kw):
    opts = options or AnalysisOptions(**kw)
    nominal = nominal_lattice(pattern, opts)
    fits = fit_alpha_peaks(pattern, opts, nominal)
    alpha = [f for f in fits if f.label in opts.reflections]
    beta = [f for f in fits if f.label.startswith("b")]
    table = pd.DataFrame([{
        "hkl": f.label, "2theta": f.center, "wG_deg": f.wg, "wL_deg": f.wl,
        "wG_err": f.wg_err, "wL_err": f.wl_err, "area": f.area, "area_err": f.area_err,
        "rwp_%": f.rwp, "at_bound": f.at_bound} for f in alpha])
    res = analyze_widths(table, pattern.wl1, instrument,
                         sample_name or pattern.source, opts)
    res.pattern = pattern
    res.alpha_fits = alpha
    res.nominal = nominal
    res.warnings[:0] = measurement_warnings(pattern, instrument)
    zero = float(getattr(instrument, "zero_shift_deg", 0.0) or 0.0) if opts.apply_zero_shift else 0.0
    res.lattice = phase_lattice(alpha, beta_for_lattice(pattern, opts, beta, nominal), pattern, zero)
    if opts.whole_profile:
        _whole_profile(res, pattern, instrument, opts, nominal)
    if beta:
        res.beta_peaks = pd.DataFrame([{"hkl": f.label, "2theta": f.center, "area": f.area,
                                        "area_err": f.area_err, "wG_deg": f.wg, "wL_deg": f.wl}
                                       for f in beta])
    return res


def measurement_warnings(pattern, instrument):
    """Wavelength assumed (not in the file) or different from the standard;
    goniometer radius different from that of the standard (another instrument);
    intensities that are not raw counts (statistical weights)."""
    out = []
    if "wavelength" in getattr(pattern, "assumed", []):
        out.append(Msg("w.wl_assumed", wl=pattern.wl1))
        name, n = ti64.best_anode(pattern)
        _, _, n_now = ti64.refine_nominal(pattern)
        if name and name != getattr(pattern, "anode", "") and n >= max(n_now + 2, 4):
            out.append(Msg("w.wl_guess", anode=name, n=n))
    wl_std = getattr(instrument, "wavelength", None)
    if wl_std and abs(wl_std[0] - pattern.wl1) > 2e-3:
        out.append(Msg("w.wl_mismatch", wl=pattern.wl1, wl_std=wl_std[0]))
    # both radii known from the files and different: another diffractometer
    r_std = getattr(instrument, "radius_mm", None)
    if (r_std and "radius" not in getattr(pattern, "assumed", ["radius"])
            and abs(float(r_std) - float(pattern.radius_mm)) > 1.0):
        out.append(Msg("w.radius_mismatch", r=pattern.radius_mm, r_std=r_std))
    # the fit weights 1/sqrt(y) assume raw counts; the data are not changed
    unit = getattr(pattern, "meta", {}).get("INTENSITY_UNIT", "counts")
    if unit != "counts":
        if unit == "non-integer":
            why = Msg("nc.nonint")
        elif unit == "low":
            why = Msg("nc.low", m=pattern.meta.get("INTENSITY_MAX", float("nan")))
        elif unit == "cps":
            why = Msg("nc.cps")
        else:
            why = Msg("nc.unit", u=unit)
        out.append(Msg("w.not_counts", why=why))
    return out


def beta_for_lattice(pattern, opts, beta, nominal=None):
    """Beta reflections for the lattice parameter: the automatic mode drops weak
    beta peaks from the profile model, but a position is still usable when the
    peak is significant (area > 3 sigma)."""
    if opts.beta == "no":
        return []
    cand = beta
    if opts.beta == "auto":
        from dataclasses import replace
        cand = [f for f in fit_alpha_peaks(pattern, replace(opts, beta="yes"), nominal) if f.label.startswith("b")]
    return [f for f in cand if np.isfinite(f.area_err) and f.area_err > 0 and f.area > 3 * f.area_err]


def phase_lattice(alpha, beta, pattern, zero_shift_deg=0.0):
    """alpha a, c, c/a (Cohen with specimen displacement) and beta a, Angstrom.
    ``zero_shift_deg`` (2theta_obs - 2theta_true of the goniometer) is
    subtracted from the peak positions first."""
    radius = float(getattr(pattern, "radius_mm", 0) or pattern.meta.get("GONIOMETER_RADIUS", 250.0))
    use = [f for f in alpha if not f.at_bound]
    if len(use) < 4:
        return {}
    z = float(zero_shift_deg or 0.0)
    lat = ti64.fit_hcp_lattice_displacement([f.center - z for f in use], [ti64.hkl_of(f.label) for f in use],
                                            pattern.wl1, radius)
    ab, ab_err, nb = ti64.beta_lattice([(f.label, f.center - z, f.center_err) for f in beta], pattern.wl1,
                                       lat["disp_um"], radius)
    lat.update({"a_beta": ab, "a_beta_err": ab_err, "n_beta": nb, "radius_mm": radius, "zero_shift_deg": z})
    return lat


def _chain(tt, wg_deg, wl_deg, l, wl_nm, a_nm, inst, opts, b2c_override=None, pop=None):
    K, wg_m = ti64.to_k(tt, wg_deg, wl_nm)
    _, wl_m = ti64.to_k(tt, wl_deg, wl_nm)
    wg_t, wl_t, flags = correct(K, wg_m, wl_m, inst)
    dK = voigt_fwhm(wg_t, wl_t)
    mwh = None
    if opts.mwh_mode == "constrained":
        try:
            mwh, _, _ = fit_mwh_population(K, dK, l, a_nm, opts.exclude_subsystems)
        except ValueError:
            mwh = None          # no anisotropic (dislocation) broadening found
    if mwh is None:
        mwh = fit_mwh(K, dK, l, a_nm)
    if pop is None:
        pop = solve_population(mwh.q1, mwh.q2, opts.contrast_method, opts.exclude_subsystems)
    b2c = pop.b2c_hk0 if b2c_override is None else b2c_override
    # contrast of each reflection from the physical population solution; it
    # equals the measured q when that lies inside the attainable region
    chkl = contrast_hkl(b2c, *pop.q_reproduced, mwh.x)
    mwa = run_mwa(K, wg_t, wl_t, chkl, opts.fourier_mode, a_min=opts.a_min,
                  limit_to_Re=opts.limit_L_to_Re)
    return K, wg_m, wl_m, wg_t, wl_t, dK, flags, mwh, pop, chkl, mwa


def analyze_widths(table, wl_A, instrument, sample_name="sample", options=None, **kw):
    """Analysis from a peak table with columns hkl, 2theta, wG_deg, wL_deg
    (optional wG_err, wL_err, area). Lets externally fitted widths be used."""
    opts = options or AnalysisOptions(**kw)
    t = table[table["hkl"].isin(opts.reflections)].reset_index(drop=True)
    warnings = []
    wl_nm = wl_A / 10.0
    hkls = [ti64.hkl_of(h) for h in t["hkl"]]
    l = np.array([h[2] for h in hkls])
    a_A, c_A = ti64.fit_hcp_lattice(t["2theta"].values, hkls, wl_A)
    a_nm = a_A / 10.0
    tt, wgd, wld = t["2theta"].values, t["wG_deg"].values, t["wL_deg"].values

    K, wg_m, wl_m, wg_t, wl_t, dK, flags, mwh, pop, chkl, mwa = _chain(
        tt, wgd, wld, l, wl_nm, a_nm, instrument, opts)

    mwh_free = fit_mwh(K, dK, l, a_nm)
    combos = combinations_summary(mwh_free.q1, mwh_free.q2)
    if combos is not None:
        combos = {k: v for k, v in combos.items() if k != "rows"}

    t["K"] = K
    t["wG_m"], t["wL_m"] = wg_m, wl_m
    t["wG_t"], t["wL_t"] = wg_t, wl_t
    t["dK_R"] = dK
    t["x"] = mwh.x
    t["b2C_hkl"] = chkl
    t["sample/instr"] = flags["ratio"]

    # ---- validity rules (spec section 3.8) ----
    valid = True
    if len(t) < 5:
        warnings.append(Msg("w.few_peaks", n=len(t)))
        valid = False
    if "at_bound" in t and t["at_bound"].any():
        warnings.append(Msg("w.width_bound", hkl=", ".join(t.loc[t["at_bound"], "hkl"])))
    for name, key in (("Gauss", "gauss_negative"), ("Lorentz", "lorentz_negative")):
        bad = list(t["hkl"][flags[key]])
        if bad:
            warnings.append(Msg("w.comp_below", comp=name, hkl=", ".join(bad)))
    low = list(t["hkl"][flags["ratio"] < 1.5])
    if low:
        warnings.append(Msg("w.ratio_low", hkl=", ".join(low)))
        if len(low) >= 3:
            warnings.append(Msg("w.detection"))
    if flags["outside_standard_range"].any():
        warnings.append(Msg("w.outside_std"))
    if mwh.r2 < 0.8:
        warnings.append(Msg("w.mwh_poor", r2=mwh.r2))
    if not pop.physical:
        warnings.append(Msg("w.q_unphysical", q1=mwh.q1, q2=mwh.q2))
    if np.any(chkl <= 0):
        warnings.append(Msg("w.chkl_neg"))
        valid = False
    if not (mwa.slope > 0):
        warnings.append(Msg("w.mwa_slope"))
        valid = False
    if mwa.n_positive_Y:
        warnings.append(Msg("w.mwa_posY", n=mwa.n_positive_Y))
    if np.isfinite(mwa.M) and not (0.5 <= mwa.M <= 10):
        warnings.append(Msg("w.mwa_M", M=mwa.M))
    if len(mwa.L) < 5:
        warnings.append(Msg("w.mwa_fewL"))
        valid = False

    # ---- texture ----
    tex, flagged = ({}, [])
    if "area" in t and t["area"].notna().all():
        try:
            tex, flagged = harris(list(t["hkl"]), list(t["area"]))
        except KeyError:
            pass
    if flagged:
        warnings.append(Msg("w.texture", hkl=", ".join(flagged)))

    # ---- Monte Carlo uncertainty ----
    mc = {}
    if opts.mc_draws and valid and {"wG_err", "wL_err"} <= set(t.columns):
        rng = np.random.default_rng(opts.seed)
        rhos = []
        eg = np.nan_to_num(t["wG_err"].values, nan=0.0)
        el = np.nan_to_num(t["wL_err"].values, nan=0.0)
        for _ in range(opts.mc_draws):
            g = np.abs(wgd + rng.normal(0, 1, len(wgd)) * eg)
            lo_ = np.abs(wld + rng.normal(0, 1, len(wld)) * el)
            b2c = rng.uniform(pop.b2c_min, pop.b2c_max) if pop.b2c_max > pop.b2c_min else pop.b2c_hk0
            try:
                out = _chain(tt, g, lo_, l, wl_nm, a_nm, instrument, opts, b2c_override=b2c, pop=pop)
                if out[-1].slope > 0 and np.all(out[9] > 0):
                    rhos.append(out[-1].rho)
            except Exception:
                continue
        if rhos:
            r = np.array(rhos)
            mc = {"n": len(r), "median": float(np.median(r)), "p16": float(np.percentile(r, 16)),
                  "p84": float(np.percentile(r, 84)), "valid_fraction": len(r) / opts.mc_draws}
            if mc["valid_fraction"] < 0.8:
                warnings.append(Msg("w.mc_unstable", pct=100 * mc["valid_fraction"]))

    sens = l_range_sensitivity(K, wg_t, wl_t, chkl, opts.fourier_mode)
    vals = [v[0] for v in sens.values() if np.isfinite(v[0])]
    if valid and vals and max(vals) / min(vals) > 2:
        warnings.append(Msg("w.L_sensitive", lo=min(vals), hi=max(vals)))
    return AnalysisResult(sample_name, t, a_A, c_A, mwh, pop, mwa, tex, warnings, valid, mc,
                          sens, opts, mwh_free=mwh_free, combos=combos)


def _whole_profile(res, pattern, instrument, opts, nominal=None):
    """Main result: Wilkens whole-profile fit.

    1. Free fit (best of several starts). If neither rho nor M* is at a bound,
       this is the result, with a Jacobian 95 % interval.
    2. Otherwise M* is fixed at ``wp_M_ref``; the interval covers the
       statistical error and M* in ``wp_M_band``.
    3. If rho then goes to its lower bound (no detectable dislocation
       broadening) a profile-likelihood scan gives the 95 % upper limit.
    """
    from .wholeprofile import fit_whole_profile, interval_from_profile, rho_profile
    kw = dict(reflections=opts.reflections, exclude=opts.exclude_subsystems, nominal=nominal)

    def best_of(fix=None, starts=opts.wp_starts):
        best = None
        for lr in starts:
            try:
                r = fit_whole_profile(pattern, instrument, start={"log_rho": lr}, fix=fix, **kw)
            except Exception as e:  # pragma: no cover
                res.warnings.append(Msg("w.wp_failed", err=e))
                continue
            if best is None or r.params["chi2"] < best.params["chi2"] - 1e-6:
                best = r
        return best

    def no_result(step):
        # every start failed: no whole-profile result and no interval (res.wp
        # stays None); nothing is substituted
        res.warnings.append(Msg("w.wp_no_result", step=step))

    free = best_of()
    if free is None:
        no_result(Msg("w.step_free"))
        return
    hit = [w for w in free.warnings if getattr(w, "kw", {}).get("name") in ("rho", "M*")]
    if not hit and np.isfinite(free.params["log_rho_err"]) and free.params["log_rho_err"] < 0.2:
        best = free
        e = best.params["log_rho_err"]
        lr0 = np.log10(best.rho)
        res.wp_interval = (10 ** (lr0 - 1.96 * e), 10 ** (lr0 + 1.96 * e))
        res.wp_interval_method = Msg("im.jacobian")
    else:
        fixM = lambda M: {"log_M": float(np.log10(M))}
        best = best_of(fixM(opts.wp_M_ref), starts=opts.wp_starts[:2])
        res.warnings.append(Msg("w.wp_fixed", why=list(hit) or Msg("w.large_error"),
                                M=opts.wp_M_ref, lo=opts.wp_M_band[0], hi=opts.wp_M_band[1]))
        res.warnings.append(Msg("w.wp_fixed_ref", M=opts.wp_M_ref))
        if best is None:
            no_result(Msg("w.step_fixed", M=opts.wp_M_ref))
            return
        if best.rho < 2e13:
            # conservative upper limit: the smallest M* of the band broadens
            # least per unit rho
            Mc = opts.wp_M_band[0]
            ref = best_of(fixM(Mc), starts=opts.wp_starts[:1])
            if ref is None:
                no_result(Msg("w.step_fixed", M=Mc))
                return
            grid = np.arange(np.floor(8 * np.log10(ref.rho)) / 8, 16.01, 0.125)
            g, chi2 = rho_profile(pattern, instrument, grid, best=ref, fix=fixM(Mc), stop_delta=25, **kw)
            # the best fit itself belongs to the profile (it may lie below the grid)
            g = np.r_[np.log10(ref.rho), g]
            chi2 = np.r_[ref.params["chi2"], chi2]
            c0 = min(ref.params["chi2"], chi2.min())
            _, hi = interval_from_profile(g, chi2, c0, ref.params["dof"])
            res.wp_interval = (np.nan, hi if hi is not None else np.nan)
            res.wp_interval_method = Msg("im.upper", M=Mc)
        else:
            vals = []
            for M in opts.wp_M_band:
                r = best_of(fixM(M), starts=(np.log10(best.rho),))
                if r is None:
                    # the interval must cover the whole band; without this end
                    # it cannot be given
                    no_result(Msg("w.step_fixed", M=M))
                    return
                e = r.params["log_rho_err"] if np.isfinite(r.params["log_rho_err"]) else 0.0
                vals += [np.log10(r.rho) - 1.96 * e, np.log10(r.rho) + 1.96 * e]
            e = best.params["log_rho_err"] if np.isfinite(best.params["log_rho_err"]) else 0.0
            vals += [np.log10(best.rho) - 1.96 * e, np.log10(best.rho) + 1.96 * e]
            res.wp_interval = (10 ** min(vals), 10 ** max(vals))
            res.wp_interval_method = Msg("im.fixed", M=opts.wp_M_ref, lo=opts.wp_M_band[0], hi=opts.wp_M_band[1])
    res.wp = best
    for w in best.warnings:
        res.warnings.append(w)
    if best.rho < 2e13:
        res.warnings.append(Msg("w.wp_below"))
    gof = best.params["chi2"] / best.params["dof"]
    if gof > 3:
        res.warnings.append(Msg("w.wp_gof", gof=gof))
