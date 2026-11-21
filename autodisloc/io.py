# SPDX-License-Identifier: MIT
# AutoDisloc 2 - Copyright (c) 2026 Firat Memu
"""Reading diffraction patterns and their measurement metadata.

Formats: Bruker DIFFRAC plus RAW v1.01 (binary), Bruker UXD (text),
PANalytical XRDML (XML) and plain two-column text/CSV files.

What a file says about the measurement (wavelengths, Ka2/Ka1 ratio,
goniometer radius, anode) is read automatically. Anything a file does not
contain is assumed (Cu Ka, ratio 0.5, R = 250 mm) and listed in
``pattern.assumed``; every value can be overridden by the user
(``read_pattern(..., radiation=..., radius_mm=..., ka2_stripped=...)``).

The least-squares weights of the fits (1/sqrt(y)) assume raw counts.
``pattern.meta["INTENSITY_UNIT"]`` records what the file says or what the
values suggest: "counts", "cps" (declared counts per second), another unit
declared by the file, "non-integer" (values that cannot be raw counts, e.g.
normalised, averaged or Ka2-stripped data) or "low" (maximum below
LOW_COUNTS_MAX and the file does not state that the values are counts). ``pattern.raw_counts`` is False for everything but "counts";
the analysis then warns (pipeline.measurement_warnings). The data and the
weights are not changed.
"""

import os
import re
import struct
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field

import numpy as np

# Characteristic wavelengths (Angstrom), International Tables for Crystallography Vol. C
ANODES = {
    "Cu": (1.540598, 1.544426),
    "Co": (1.788965, 1.792850),
    "Fe": (1.936042, 1.939980),
    "Cr": (2.289700, 2.293606),
    "Mo": (0.709300, 0.713590),
    "Ag": (0.559421, 0.563813),
}
CU_KA1, CU_KA2 = ANODES["Cu"]
DEFAULT_RADIUS_MM = 250.0
# a pattern whose highest intensity is below this is unlikely to be raw counts
LOW_COUNTS_MAX = 100.0


@dataclass
class Pattern:
    two_theta: np.ndarray          # degrees
    counts: np.ndarray
    wl1: float = CU_KA1            # Angstrom
    wl2: float = CU_KA2
    ka2_ratio: float = 0.5         # I(Ka2)/I(Ka1); 0 means Ka2 already stripped
    source: str = ""
    meta: dict = field(default_factory=dict)
    radius_mm: float = DEFAULT_RADIUS_MM
    anode: str = "Cu"
    fmt: str = ""
    assumed: list = field(default_factory=list)   # keys not found in the file

    @property
    def ka2_stripped(self):
        return self.ka2_ratio == 0.0

    @property
    def wl1_nm(self):
        return self.wl1 / 10.0

    @property
    def raw_counts(self):
        """True when the intensities are (consistent with) raw counts."""
        return self.meta.get("INTENSITY_UNIT", "counts") == "counts"


def anode_of(wl1):
    """Anode whose Ka1 matches wl1 within 0.002 Angstrom, else ''."""
    for k, (a1, _) in ANODES.items():
        if abs(a1 - wl1) < 0.002:
            return k
    return ""


def read_pattern(path, ka2_stripped=None, radiation=None, radius_mm=None):
    """Read a pattern with its metadata.

    ka2_stripped : None = from the file, True/False = override.
    radiation    : None = from the file, an anode name ("Cu", "Co", ...) or
                   a tuple (wl1, wl2[, ratio]) in Angstrom = override.
    radius_mm    : goniometer radius override.
    """
    ext = os.path.splitext(path)[1].lower()
    with open(path, "rb") as f:
        head = f.read(512)
    if head.startswith(b"RAW1.01"):
        pat = _read_raw101(path)
    elif head[:4] in (b"RAW4", b"RAW ") or head.startswith(b"RAW2") or head.startswith(b"RAW3"):
        raise ValueError(f"{os.path.basename(path)}: Bruker RAW version {head[:7].decode('latin-1', 'replace')} "
                         "is not supported; export the scan as .uxd, .xy or .brml-converted text.")
    elif ext == ".uxd":
        pat = _read_uxd(path)
    elif ext == ".xrdml" or b"<xrdMeasurements" in head:
        pat = _read_xrdml(path)
    else:
        pat = _read_xy(path)
    if radiation is not None:
        if isinstance(radiation, str):
            pat.wl1, pat.wl2 = ANODES[radiation]
        else:
            pat.wl1, pat.wl2 = float(radiation[0]), float(radiation[1])
            if len(radiation) > 2 and radiation[2] is not None:
                pat.ka2_ratio = float(radiation[2])
        pat.assumed = [a for a in pat.assumed if a != "wavelength"]
        pat.meta["RADIATION_OVERRIDE"] = True
    if radius_mm is not None:
        pat.radius_mm = float(radius_mm)
        pat.assumed = [a for a in pat.assumed if a != "radius"]
    if ka2_stripped is not None:
        pat.ka2_ratio = 0.0 if ka2_stripped else (pat.ka2_ratio or 0.5)
        pat.assumed = [a for a in pat.assumed if a != "ka2"]
    pat.anode = anode_of(pat.wl1) or "?"
    order = np.argsort(pat.two_theta)
    pat.two_theta = pat.two_theta[order]
    pat.counts = pat.counts[order]
    pat.meta["INTENSITY_UNIT"] = intensity_unit(pat.counts, pat.meta.get("INTENSITY_UNIT"))
    pat.meta["INTENSITY_MAX"] = float(np.max(pat.counts)) if len(pat.counts) else float("nan")
    return pat


def intensity_unit(y, declared=None):
    """Classify the intensities (see the module docstring). ``declared`` is
    the unit given by the file, if any ("counts", "cps" or another string)."""
    if declared and declared != "counts":
        return declared
    y = np.asarray(y, float)
    finite = y[np.isfinite(y)]
    if finite.size == 0:
        return "non-integer"
    if np.any(np.abs(finite - np.round(finite)) > 1e-6):
        return "non-integer"
    # a small maximum only hints at scaled data; a file that states "counts" is believed
    if declared != "counts" and finite.max() < LOW_COUNTS_MAX:
        return "low"
    return "counts"


def describe(pattern):
    """Measurement metadata for display: list of (key, value, from_file)."""
    from .i18n import tr
    a = set(pattern.assumed)
    x = pattern.two_theta
    step = float(np.median(np.diff(x))) if len(x) > 1 else float("nan")
    return [
        ("format", tr("meta.xy") if pattern.fmt == "2-column text" else pattern.fmt, True),
        ("anode", pattern.anode, "wavelength" not in a),
        ("wl1", f"{pattern.wl1:.6f} Å", "wavelength" not in a),
        ("wl2", f"{pattern.wl2:.6f} Å", "wavelength" not in a),
        ("ka2", f"{pattern.ka2_ratio:.3f}" + (f" ({tr('ka2.stripped')})" if pattern.ka2_stripped else ""),
         "ka2" not in a),
        ("radius", f"{pattern.radius_mm:.1f} mm", "radius" not in a),
        ("range", f"{x.min():.2f}–{x.max():.2f}°", True),
        ("step", f"{step:.4f}°", True),
        ("points", f"{len(x)}", True),
    ]


def _read_uxd(path):
    meta = {}
    tt, cnt = [], []
    in_data = False
    counts_only = False
    with open(path, "r", encoding="latin-1") as f:
        for line in f:
            s = line.strip()
            if not s or s.startswith(";"):
                continue
            if s.startswith("_"):
                key = s[1:].split("=", 1)[0].strip()
                if key in ("2THETACOUNTS", "2THETACPS"):
                    in_data, counts_only = True, False
                    meta["INTENSITY_UNIT"] = "cps" if key.endswith("CPS") else "counts"
                    continue
                if key in ("COUNTS", "CPS"):
                    in_data, counts_only = True, True
                    meta["INTENSITY_UNIT"] = "cps" if key == "CPS" else "counts"
                    continue
                if "=" in s:
                    k, v = s[1:].split("=", 1)
                    meta[k.strip()] = v.strip().strip("'")
                in_data = False
                continue
            if not in_data:
                continue
            parts = re.split(r"[;,\s]+", s)
            try:
                vals = [float(p) for p in parts if p]
            except ValueError:
                continue
            if counts_only:
                cnt.extend(vals)
            elif len(vals) >= 2:
                tt.append(vals[0])
                cnt.append(vals[1])
    cnt = np.asarray(cnt, float)
    if counts_only or not tt:
        start = float(meta.get("START", meta.get("2THETA", 0.0)))
        step = float(meta.get("STEPSIZE", 0.02))
        tt = start + step * np.arange(len(cnt))
    assumed = [k for k, m in (("wavelength", "WL1"), ("ka2", "WLRATIO"), ("radius", "GONIOMETER_RADIUS"))
               if m not in meta]
    pat = Pattern(np.asarray(tt, float), cnt, float(meta.get("WL1", CU_KA1)), float(meta.get("WL2", CU_KA2)),
                  float(meta.get("WLRATIO", 0.5)), path, meta,
                  float(meta.get("GONIOMETER_RADIUS", DEFAULT_RADIUS_MM)), fmt="Bruker UXD", assumed=assumed)
    return pat


def _read_raw101(path):
    """Bruker DIFFRAC plus RAW v1.01: 712-byte file header, then per range a
    header (length at +0, step count at +4, start 2theta at +16, step at +176,
    supplementary header length at +256) followed by float32 counts. The file
    header holds the goniometer radius (float32 at 564) and the Ka1, Ka2, Kb
    wavelengths and the Ka2/Ka1 ratio (float64 at 624, 632, 640, 648); DIFFRAC
    (EVA) sets the ratio to 0 when it strips Ka2, exactly as _WLRATIO in UXD."""
    d = open(path, "rb").read()
    n_ranges = struct.unpack_from("<i", d, 12)[0]
    off = 712
    tt, cnt = [], []
    for _ in range(max(n_ranges, 1)):
        hlen, nsteps = struct.unpack_from("<ii", d, off)
        start = struct.unpack_from("<d", d, off + 16)[0]
        step = struct.unpack_from("<d", d, off + 176)[0]
        sup = struct.unpack_from("<i", d, off + 256)[0]
        data_off = off + hlen + sup
        y = np.frombuffer(d, dtype="<f4", count=nsteps, offset=data_off).astype(float)
        tt.append(start + step * np.arange(nsteps))
        cnt.append(y)
        off = data_off + 4 * nsteps
        if off >= len(d):
            break
    meta = {"FORMAT": "RAW1.01", "RANGES": n_ranges}
    assumed = []
    wl1, wl2, ratio = CU_KA1, CU_KA2, 0.5
    w1, w2, _, r = struct.unpack_from("<dddd", d, 624) if len(d) >= 656 else (0, 0, 0, -1)
    if 0.3 < w1 < 3.0 and 0.3 < w2 < 3.0 and 0.0 <= r <= 1.0:
        wl1, wl2, ratio = w1, w2, r
        meta.update({"WL1": w1, "WL2": w2, "WLRATIO": r})
    else:
        assumed += ["wavelength", "ka2"]
    radius = struct.unpack_from("<f", d, 564)[0] if len(d) >= 568 else 0.0
    if 100.0 < radius < 600.0:
        meta["GONIOMETER_RADIUS"] = radius
    else:
        radius = DEFAULT_RADIUS_MM
        assumed.append("radius")
    return Pattern(np.concatenate(tt), np.concatenate(cnt), wl1, wl2, ratio, path, meta, float(radius),
                   fmt="Bruker RAW 1.01", assumed=assumed)


def _local(tag):
    return tag.rsplit("}", 1)[-1]


def _read_xrdml(path):
    """PANalytical XRDML (any schema version; namespace ignored). The first
    scan is read; positions from start/end or a list, intensities or counts
    (divided by the counting time is not needed: profile shapes only)."""
    root = ET.parse(path).getroot()
    find = lambda el, name: next((e for e in el.iter() if _local(e.tag) == name), None)
    meta = {"FORMAT": "XRDML"}
    assumed = []
    wl = find(root, "usedWavelength")
    wl1, wl2, ratio = CU_KA1, CU_KA2, 0.5
    if wl is not None and find(wl, "kAlpha1") is not None:
        wl1 = float(find(wl, "kAlpha1").text)
        wl2 = float(find(wl, "kAlpha2").text) if find(wl, "kAlpha2") is not None else wl1
        r = find(wl, "ratioKAlpha2KAlpha1")
        ratio = float(r.text) if r is not None else 0.5
        intended = wl.attrib.get("intended", "")
        if re.sub(r"[\s\-_]", "", intended).lower().endswith("alpha1"):
            ratio = 0.0          # "K-Alpha 1": monochromatised (Ka1 only) data
        meta.update({"WL1": wl1, "WL2": wl2, "WLRATIO": ratio, "INTENDED": intended})
    else:
        assumed += ["wavelength", "ka2"]
    rad = find(root, "radius")
    radius = float(rad.text) if rad is not None else DEFAULT_RADIUS_MM
    if rad is None:
        assumed.append("radius")
    an = find(root, "anodeMaterial")
    if an is not None:
        meta["ANODE"] = an.text
    tube = find(root, "xRayTube")
    if tube is not None:
        meta["TUBE"] = tube.attrib.get("name", "")
    scan = find(root, "scan")
    dp = find(scan if scan is not None else root, "dataPoints")
    y = None
    for name in ("intensities", "counts"):
        e = find(dp, name)
        if e is not None and e.text:
            y = np.array(e.text.split(), float)
            unit = e.attrib.get("unit", "").strip()
            if unit:
                meta["INTENSITY_UNIT"] = "counts" if unit.lower() == "counts" else unit
            break
    if y is None:
        raise ValueError(f"{os.path.basename(path)}: no intensities in XRDML file")
    tt = None
    for pos in dp.iter():
        if _local(pos.tag) == "positions" and pos.attrib.get("axis") == "2Theta":
            lp = find(pos, "listPositions")
            if lp is not None and lp.text:
                tt = np.array(lp.text.split(), float)
            else:
                a, b = float(find(pos, "startPosition").text), float(find(pos, "endPosition").text)
                tt = np.linspace(a, b, len(y))
            break
    if tt is None:
        raise ValueError(f"{os.path.basename(path)}: no 2Theta positions in XRDML file")
    return Pattern(tt, y, wl1, wl2, ratio, path, meta, radius, fmt="PANalytical XRDML", assumed=assumed)


_XY_KEYS = {"WL1": "WL1", "LAMBDA1": "WL1", "WL2": "WL2", "LAMBDA2": "WL2", "WLRATIO": "WLRATIO",
            "KA2_RATIO": "WLRATIO", "RADIUS": "GONIOMETER_RADIUS", "GONIOMETER_RADIUS": "GONIOMETER_RADIUS",
            "ANODE": "ANODE"}


def _read_xy(path):
    """Two numeric columns (2theta, counts); separators: space, tab, comma,
    semicolon. Optional header lines (starting with # or ;) may give the
    measurement data as KEY = value: WL1, WL2 (Angstrom), WLRATIO (Ka2/Ka1,
    0 = stripped), ANODE (Cu, Co, ...), RADIUS (goniometer radius, mm)."""
    rows, meta = [], {"FORMAT": "xy"}
    with open(path, "r", encoding="latin-1") as f:
        for line in f:
            st = line.strip()
            if st[:1] in ("#", ";", "!"):
                m = re.match(r"[#;!]\s*([A-Za-z_0-9]+)\s*[=:]\s*([^\s#;]+)", st)
                if m and m.group(1).upper() in _XY_KEYS:
                    meta[_XY_KEYS[m.group(1).upper()]] = m.group(2)
                continue
            parts = re.split(r"[;,\s\t]+", st)
            try:
                vals = [float(p) for p in parts if p]
            except ValueError:
                continue
            if len(vals) >= 2:
                rows.append(vals[:2])
    if not rows:
        raise ValueError(f"{os.path.basename(path)}: no two-column numeric data found")
    arr = np.asarray(rows, float)
    assumed = []
    wl1, wl2, ratio, radius = CU_KA1, CU_KA2, 0.5, DEFAULT_RADIUS_MM
    try:
        if "WL1" in meta:
            wl1 = float(meta["WL1"])
            wl2 = float(meta.get("WL2", wl1))
        elif meta.get("ANODE", "").capitalize() in ANODES:
            wl1, wl2 = ANODES[meta["ANODE"].capitalize()]
        else:
            assumed.append("wavelength")
        if "WLRATIO" in meta:
            ratio = float(meta["WLRATIO"])
        else:
            assumed.append("ka2")
        if "GONIOMETER_RADIUS" in meta:
            radius = float(meta["GONIOMETER_RADIUS"])
        else:
            assumed.append("radius")
    except ValueError as e:
        raise ValueError(f"{os.path.basename(path)}: invalid header value ({e})")
    return Pattern(arr[:, 0], arr[:, 1], wl1, wl2, ratio, source=path, meta=meta, radius_mm=radius,
                   fmt="2-column text", assumed=assumed)
