# SPDX-License-Identifier: MIT
# AutoDisloc 2 - Copyright (c) 2026 Firat Memu
"""Average dislocation contrast factors of hexagonal Ti and Burgers-vector
population analysis (Dragomir & Ungar, J. Appl. Cryst. 35 (2002) 556, Table 2
and Eqs. 8-13).

C_hk.l = C_hk.0 (1 + q1 x + q2 x^2),   x = (2/3) (l / (K a))^2

For a mixture of sub-slip systems with fractions f_i >= 0, sum f_i = 1:
    b^2C_hk.0 = sum f_i C_i b_i^2
    q_j       = sum f_i C_i b_i^2 q_j(i) / b^2C_hk.0
so the attainable (q1, q2) are the convex hull of the sub-system points.
"""

from dataclasses import dataclass, field

import numpy as np
from scipy.optimize import linprog, minimize, nnls

from .i18n import Msg

BURGERS_NM = {"a": 0.295, "c": 0.468, "c+a": 0.553}

# name: (Burgers type, C_hk.0, q1, q2) -- titanium, Dragomir & Ungar 2002
TI_SUBSYSTEMS = {
    "BE":   ("a",   0.20227, -0.101142, -0.102623),
    "PrE":  ("a",   0.35387, -1.19272,   0.355623),
    "PyE":  ("a",   0.3118,  -0.894009,  0.1833109),
    "S1":   ("a",   0.1444,   0.59492,  -0.710368),
    "Pr2E": ("c",   0.04853,  3.61619,   1.226411),
    "S3":   ("c",   3.61e-6,  165366.0, -98611.0),
    "Pr3E": ("c+a", 0.10247,  2.01717,  -0.616631),
    "PY2E": ("c+a", 0.09227,  1.299046,  0.3972469),
    "PY3E": ("c+a", 0.09813,  1.894120, -0.365739),
    "PY4E": ("c+a", 0.09323,  1.5270212, 0.146150),
    "S2":   ("c+a", 0.41873,  1.25714,  -0.94015),
}


def x_param(l, K, a_nm):
    return (2.0 / 3.0) * (np.asarray(l) / (np.asarray(K) * a_nm)) ** 2


def contrast_hkl(b2c_hk0, q1, q2, x):
    """b^2 C_hkl for each reflection (nm^2)."""
    x = np.asarray(x)
    return b2c_hk0 * (1.0 + q1 * x + q2 * x * x)


def _table(names):
    w = np.array([TI_SUBSYSTEMS[n][1] * BURGERS_NM[TI_SUBSYSTEMS[n][0]] ** 2 for n in names])
    q1 = np.array([TI_SUBSYSTEMS[n][2] for n in names])
    q2 = np.array([TI_SUBSYSTEMS[n][3] for n in names])
    types = [TI_SUBSYSTEMS[n][0] for n in names]
    return w, q1, q2, types


@dataclass
class PopulationResult:
    method: str
    b2c_hk0: float               # central value, nm^2
    b2c_min: float
    b2c_max: float
    h: dict                      # Burgers-type fractions (central)
    h_min: dict
    h_max: dict
    q_reproduced: tuple
    residual: float              # (dq1^2 + dq2^2) of the best solution
    physical: bool               # measured q inside the attainable region
    fractions: dict = field(default_factory=dict)  # sub-system fractions (central)
    n_solutions: int = 1


def _q_of(f, w, q1, q2):
    ww = f * w
    s = ww.sum()
    return (ww * q1).sum() / s, (ww * q2).sum() / s


def subsystem_range(q1m, q2m, exclude=("S3",)):
    """Exact range of b^2C_hk0 and of the Burgers-type fractions over *all*
    sub-system mixtures that reproduce (q1m, q2m). Because q is a ratio of
    linear forms, the constraints are linear in f and the extremes follow from
    linear programming. Returns None when no mixture reproduces q."""
    names = [n for n in TI_SUBSYSTEMS if n not in exclude]
    w, Q1, Q2, types = _table(names)
    A_eq = np.vstack([w * (Q1 - q1m), w * (Q2 - q2m), np.ones_like(w)])
    b_eq = np.array([0.0, 0.0, 1.0])
    out = {}
    objectives = {"b2c": w}
    objectives.update({t: np.array([1.0 if tt == t else 0.0 for tt in types]) for t in BURGERS_NM})
    for key, c in objectives.items():
        lo = linprog(c, A_eq=A_eq, b_eq=b_eq, bounds=[(0, None)] * len(w), method="highs")
        hi = linprog(-c, A_eq=A_eq, b_eq=b_eq, bounds=[(0, None)] * len(w), method="highs")
        if not (lo.success and hi.success):
            return None
        out[key] = (float(c @ lo.x), float(c @ hi.x))
        if key == "b2c":
            out["f_mid"] = dict(zip(names, map(float, 0.5 * (lo.x + hi.x))))
    return out


def _project(q1m, q2m, exclude):
    """Closest attainable (q1, q2) when the measured pair is outside the
    attainable region; returns sub-system fractions."""
    names = [n for n in TI_SUBSYSTEMS if n not in exclude]
    w, Q1, Q2, types = _table(names)

    def obj(f):
        a, b = _q_of(np.abs(f) + 1e-15, w, Q1, Q2)
        return (a - q1m) ** 2 + (b - q2m) ** 2
    rng = np.random.default_rng(0)
    best = None
    for _ in range(60):
        r = minimize(obj, rng.dirichlet(np.ones(len(names))), method="SLSQP",
                     bounds=[(0.0, 1.0)] * len(names),
                     constraints=({"type": "eq", "fun": lambda f: f.sum() - 1.0},),
                     options={"ftol": 1e-14, "maxiter": 500})
        f = np.clip(r.x, 0, None)
        f = f / f.sum()
        if best is None or obj(f) < best[0]:
            best = (obj(f), f)
    return names, w, Q1, Q2, types, best[1], best[0]


def _type_table(names, w, Q1, Q2, types):
    P, T1, T2, tlist = [], [], [], []
    for t in BURGERS_NM:
        idx = [k for k, tt in enumerate(types) if tt == t]
        if not idx:
            continue
        c = np.array([TI_SUBSYSTEMS[names[k]][1] for k in idx])
        P.append(c.mean() * BURGERS_NM[t] ** 2)
        T1.append((c * Q1[idx]).sum() / c.sum())
        T2.append((c * Q2[idx]).sum() / c.sum())
        tlist.append(t)
    return np.array(P), np.array(T1), np.array(T2), tlist


def solve_population(q1m, q2m, method="type_average", exclude=("S3",)):
    """Burgers-vector population and b^2C_hk0.

    method="type_average" (default): Dragomir & Ungar 2002 Eqs. 10-13 -- the
    contrast factors are averaged over the sub-systems of each Burgers type
    (random population inside a type) giving a determined 3-unknown problem;
    this is also the procedure of Muiruri et al. 2020, Appendix A.
    method="subsystems": centre of the exact range over all sub-system mixtures.

    In both cases the exact range over all sub-system mixtures (linear
    programming) is attached as b2c_min/b2c_max and h_min/h_max.
    """
    names = [n for n in TI_SUBSYSTEMS if n not in exclude]
    w, Q1, Q2, types = _table(names)
    rng_ = subsystem_range(q1m, q2m, exclude)
    zero = {t: 0.0 for t in BURGERS_NM}

    if method == "type_average":
        P, T1, T2, tlist = _type_table(names, w, Q1, Q2, types)
        M = np.vstack([P * (T1 - q1m), P * (T2 - q2m), 10.0 * np.ones_like(P)])
        h, _ = nnls(M, np.array([0.0, 0.0, 10.0]))
        h = h / h.sum()
        b2c = float((h * P).sum())
        qr = ((h * P * T1).sum() / b2c, (h * P * T2).sum() / b2c)
        res = (qr[0] - q1m) ** 2 + (qr[1] - q2m) ** 2
        hd = dict(zero, **dict(zip(tlist, map(float, h))))
        physical = res < 1e-6
        label = Msg("pop.type_avg")
        fr = {}
        if not physical and rng_ is not None:
            # type-averaged contrasts cannot reproduce q, but a sub-system
            # mixture can: use the centre of the exact sub-system range
            method = "subsystems"
        if not physical and rng_ is None:
            label = Msg("pop.type_avg_outside")
    if method == "subsystems":
        if rng_ is not None:
            b2c = 0.5 * sum(rng_["b2c"])
            hd = {t: 0.5 * sum(rng_[t]) for t in BURGERS_NM}
            fr = rng_["f_mid"]
            f = np.array([fr[n] for n in names])
            qr, res, physical = _q_of(f, w, Q1, Q2), 0.0, True
            label = Msg("pop.sub_range")
        else:
            names, w, Q1, Q2, types, f, res = _project(q1m, q2m, exclude)
            b2c = float((f * w).sum())
            hd = {t: float(f[[k for k, tt in enumerate(types) if tt == t]].sum()) for t in BURGERS_NM}
            qr, physical = _q_of(f, w, Q1, Q2), False
            fr = dict(zip(names, map(float, f)))
            label = Msg("pop.sub_proj")
    if rng_ is not None:
        bmin, bmax = rng_["b2c"]
        hmin = {t: rng_[t][0] for t in BURGERS_NM}
        hmax = {t: rng_[t][1] for t in BURGERS_NM}
    else:
        bmin = bmax = b2c
        hmin = hmax = hd
    return PopulationResult(label, float(b2c), float(min(bmin, b2c)), float(max(bmax, b2c)),
                            hd, hmin, hmax, tuple(map(float, qr)), float(res), bool(physical), fr)


# ---------------------------------------------------------------------------
# "One sub-system per Burgers type" method (Dragomir & Ungar 2002, Eqs. 11-13)
# ---------------------------------------------------------------------------

def combinations(q1m, q2m, table=None):
    """Solve Dragomir Eqs. 11-13 for every combination of one <a>, one <c>
    and one <c+a> sub-system (4 x 2 x 5 = 40 for Ti), i.e. the sub-systems
    are reduced to one per Burgers type. Returns a list of dicts with
    the sub-system names, h_a, h_c, h_c+a, b2C_hk0 and 'physical'
    (all h in [0, 1])."""
    table = table or TI_SUBSYSTEMS
    by_type = {t: [n for n in table if table[n][0] == t] for t in BURGERS_NM}
    out = []
    for na in by_type["a"]:
        for nc in by_type["c"]:
            for nca in by_type["c+a"]:
                names = (na, nc, nca)
                P = np.array([table[n][1] * BURGERS_NM[table[n][0]] ** 2 for n in names])
                T1 = np.array([table[n][2] for n in names])
                T2 = np.array([table[n][3] for n in names])
                M = np.array([P * (T1 - q1m), P * (T2 - q2m), np.ones(3)])
                try:
                    h = np.linalg.solve(M, [0.0, 0.0, 1.0])
                except np.linalg.LinAlgError:
                    continue
                out.append({"a": na, "c": nc, "c+a": nca, "h_a": h[0], "h_c": h[1],
                            "h_c+a": h[2], "b2C_hk0": float(h @ P),
                            "physical": bool(np.all(h >= -1e-9) and np.all(h <= 1 + 1e-9))})
    return out


def combinations_summary(q1m, q2m, table=None):
    """Mean and standard deviation of the physical solutions among the 40
    combinations; None when no combination is physical."""
    rows = [r for r in combinations(q1m, q2m, table) if r["physical"]]
    if not rows:
        return None
    keys = ["h_a", "h_c", "h_c+a", "b2C_hk0"]
    arr = np.array([[r[k] for k in keys] for r in rows])
    return {"n": len(rows), "mean": dict(zip(keys, arr.mean(0))),
            "std": dict(zip(keys, arr.std(0, ddof=1) if len(rows) > 1 else np.zeros(4))),
            "rows": rows}


def type_parabolas(exclude=("S3",), prismatic_weight=1.0):
    """Burgers-type averaged b^2 C_hk0 (P_t) and q parameters (Dragomir Eqs.
    10-13). ``prismatic_weight`` = 2 gives the prismatic <a> sub-system double
    weight (Dragomir & Ungar 2002, Sec. 5.3, step iii)."""
    P, T1, T2 = {}, {}, {}
    for t in BURGERS_NM:
        ns = [n for n in TI_SUBSYSTEMS if TI_SUBSYSTEMS[n][0] == t and n not in exclude]
        w = np.array([prismatic_weight if n == "PrE" else 1.0 for n in ns])
        c = np.array([TI_SUBSYSTEMS[n][1] for n in ns])
        q1 = np.array([TI_SUBSYSTEMS[n][2] for n in ns])
        q2 = np.array([TI_SUBSYSTEMS[n][3] for n in ns])
        P[t] = float((w * c).sum() / w.sum() * BURGERS_NM[t] ** 2)
        T1[t] = float((w * c * q1).sum() / (w * c).sum())
        T2[t] = float((w * c * q2).sum() / (w * c).sum())
    return P, T1, T2


def population_from_h(h, exclude=("S3",), prismatic_weight=1.0):
    """b^2C_hk0, q1, q2 of a Burgers-type population h = {type: fraction}."""
    P, T1, T2 = type_parabolas(exclude, prismatic_weight)
    X = sum(h[t] * P[t] for t in P)
    q1 = sum(h[t] * P[t] * T1[t] for t in P) / X
    q2 = sum(h[t] * P[t] * T2[t] for t in P) / X
    return X, q1, q2
