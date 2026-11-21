# SPDX-License-Identifier: MIT
# AutoDisloc 2 - Copyright (c) 2026 Firat Memu
"""Command line use (English and Turkish command names are equivalent):

  python -m autodisloc instrument STANDARD.uxd -o instrument.json      (cihaz)
  python -m autodisloc analyze SAMPLE1.raw [SAMPLE2.raw ...] -c instrument.json -o report.xlsx
                                                                       (analiz)
Options: --lang tr|en, --package FOLDER (figures + tables), --ka2 auto|present|stripped,
  --radiation Cu|Co|Fe|Cr|Mo|Ag|WL1,WL2[,RATIO]  (default: from the file),
  --radius MM (goniometer radius, default: from the file),
  instrument: --standard corundum|LaB6|Si|CeO2|other, --std-lattice A[,C]
  analyze:    --material Ti-6Al-4V|CP-Ti, --lattice A,C[,A_BETA], --no-refine, --zero
"""

import argparse
import os
import sys

import numpy as np

from .i18n import default_language, set_language, tr
from .instrument import InstrumentModel, fit_instrument
from . import materials, standards
from .io import ANODES, read_pattern
from .pipeline import AnalysisOptions, analyze
from .report import write_excel

KA2 = {"auto": None, "present": False, "stripped": True}


def _radiation(v):
    if v is None or v in ANODES:
        return v
    vals = [float(x) for x in v.split(",")]
    if len(vals) not in (2, 3):
        raise argparse.ArgumentTypeError("--radiation: anode name or WL1,WL2[,RATIO]")
    return tuple(vals)


def _floats(v):
    return [float(x) for x in v.split(",")]


def _common(p):
    p.add_argument("--ka2", choices=list(KA2), default="auto")
    p.add_argument("--radiation", "--radyasyon", type=_radiation, default=None,
                   help="Cu, Co, Fe, Cr, Mo, Ag or WL1,WL2[,RATIO] in Angstrom (default: from the file)")
    p.add_argument("--radius", "--yaricap", type=float, default=None, help="goniometer radius in mm")


def main(argv=None):
    ap = argparse.ArgumentParser(prog="autodisloc")
    ap.add_argument("--lang", choices=["tr", "en"], default=default_language())
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("instrument", aliases=["cihaz"], help="instrument model from a line standard")
    c.add_argument("standard_file", metavar="STANDARD")
    c.add_argument("-o", "--out", default=None)
    c.add_argument("--degree", "--derece", type=int, default=1)
    c.add_argument("--standard", "--standart", choices=standards.STANDARD_KEYS, default="corundum")
    c.add_argument("--std-lattice", type=_floats, default=None, help="a[,c] of the standard in Angstrom")
    _common(c)
    a = sub.add_parser("analyze", aliases=["analiz"], help="dislocation density analysis")
    a.add_argument("samples", nargs="+")
    a.add_argument("-c", "--instrument", "--cihaz", required=True)
    a.add_argument("-o", "--out", default=None)
    a.add_argument("--package", "--paket", default=None, help="write the paper package to this folder")
    a.add_argument("--fourier", choices=["voigt", "eq13"], default="voigt",
                   help="A(L) of the Voigt-mWA: Voigt transform or Muiruri 2020 Eq. 13 (comparison)")
    a.add_argument("--contrast", "--kontrast", choices=["type_average", "subsystems"], default="type_average")
    a.add_argument("--amin", type=float, default=0.1)
    a.add_argument("--mc", type=int, default=200)
    a.add_argument("--mwh", choices=["constrained", "free"], default="constrained")
    _common(a)
    a.add_argument("--material", "--malzeme", choices=[k for k in materials.MATERIAL_KEYS if k != "custom"],
                   default="Ti-6Al-4V")
    a.add_argument("--lattice", "--kafes", type=_floats, default=None, help="nominal alpha a,c[,a_beta] (Angstrom)")
    a.add_argument("--beta", choices=["auto", "yes", "no"], default=None)
    a.add_argument("--no-refine", action="store_true", help="do not adjust the nominal lattice to the pattern")
    a.add_argument("--zero", action="store_true", help="correct lattice parameters for the zero shift of the standard")
    a.add_argument("--no-whole-profile", "--tam-profil-yok", action="store_true")
    args = ap.parse_args(argv)
    set_language(args.lang)

    if args.cmd in ("instrument", "cihaz"):
        out = args.out or ("cihaz.json" if args.lang == "tr" else "instrument.json")
        lat = None
        if args.std_lattice:
            lat = {"a": args.std_lattice[0], "c": args.std_lattice[1] if len(args.std_lattice) > 1 else float("nan")}
        inst = fit_instrument(args.standard_file, degree=args.degree, ka2_stripped=KA2[args.ka2],
                              standard=args.standard, lattice=lat, radiation=args.radiation, radius_mm=args.radius)
        inst.save(out)
        print(tr("cli.inst_saved", p=out))
        print(f"  Gauss   w_G,s(K) = {inst.gauss_coef}")
        print(f"  Lorentz w_L,s(K) = {inst.lorentz_coef}")
        for line in inst.describe():
            print("  " + line)
        for w in getattr(inst, "fit_warnings", []):
            print("   ! " + str(w))
        return 0

    inst = InstrumentModel.load(args.instrument)
    mat = materials.get(args.material)
    nominal = [mat.a, mat.c, mat.a_beta]
    if args.lattice:
        nominal[:len(args.lattice)] = args.lattice[:3]
    opts = AnalysisOptions(fourier_mode=args.fourier, contrast_method=args.contrast,
                           a_min=args.amin, mc_draws=args.mc, mwh_mode=args.mwh,
                           whole_profile=not args.no_whole_profile, material=args.material,
                           nominal_lattice=tuple(nominal), beta=args.beta or mat.beta,
                           refine_nominal=not args.no_refine, apply_zero_shift=args.zero)
    results = []
    for path in args.samples:
        r = analyze(read_pattern(path, ka2_stripped=KA2[args.ka2], radiation=args.radiation,
                                 radius_mm=args.radius), inst,
                    os.path.splitext(os.path.basename(path))[0], opts)
        results.append(r)
        s = r.summary()
        fmt = lambda v, f: f.format(v) if isinstance(v, float) and np.isfinite(v) else "–"
        print(tr("cli.line", s=s["sample"], rho=s["rho_text"], method=str(s["interval_method"]),
                 M=fmt(s["M_star"], "{:.2f}"), ha=fmt(s["h_a"], "{:.2f}"),
                 mwa=fmt(s["mwa_rho"], "{:.2e}"), valid=str(s["mwa_valid"])))
        for w in r.warnings:
            print("   ! " + str(w))
    out = args.out or tr("ex.report")
    write_excel(results, out, inst)
    print(tr("cli.report", p=out))
    if args.package:
        from .export import export_package
        export_package(results, args.package, inst)
        print(tr("cli.package", p=args.package))
    return 0


if __name__ == "__main__":
    sys.exit(main())
