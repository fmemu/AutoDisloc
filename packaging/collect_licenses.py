# SPDX-License-Identifier: MIT
# AutoDisloc 2 - Copyright (c) 2026 Firat Memu
"""Collect the licences of everything that the packaged application bundles.

    python packaging/collect_licenses.py OUTDIR

Run with the Python of the build environment. Writes OUTDIR/THIRD-PARTY-NOTICES.txt
(component, version, licence, homepage), OUTDIR/licenses/<component>/... (the
licence files shipped by each package), the Python licence, the GNU GPL and
LGPL texts (Qt / PySide6 are used under the LGPLv3) and OUTDIR/QT-SOURCE.txt
with the exact Qt and PySide6 source archives of this build.
"""

import importlib.metadata as md
import os
import re
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
TOP = ["numpy", "scipy", "pandas", "openpyxl", "matplotlib", "PySide6-Essentials", "pillow"]
LICENSE_NAME = re.compile(r"(LICEN[CS]E|COPYING|NOTICE|AUTHORS)", re.I)
# Qt parts that the packaged program contains (see AutoDisloc2.spec)
QT_MODULES = ["qtbase", "qtsvg", "qtimageformats"]


def norm(name):
    return re.sub(r"[-_.]+", "-", name).lower()


def runtime_closure(top):
    """Distributions needed at run time (requirements, evaluated markers, no extras)."""
    try:
        from packaging.requirements import Requirement
    except ImportError:  # pragma: no cover
        Requirement = None
    seen, todo = {}, list(top)
    while todo:
        name = todo.pop()
        key = norm(name)
        if key in seen:
            continue
        try:
            dist = md.distribution(name)
        except md.PackageNotFoundError:
            continue
        seen[key] = dist
        for req in dist.requires or []:
            if Requirement is None:
                todo.append(re.split(r"[ ;<>=!~\[]", req, 1)[0])
                continue
            r = Requirement(req)
            if r.marker is not None and not r.marker.evaluate({"extra": ""}):
                continue
            todo.append(r.name)
    return seen


KNOWN = {"matplotlib": "Matplotlib License (PSF-based); bundled fonts: DejaVu, STIX (OFL), BaKoMa"}


def licence_of(dist):
    """Short licence name: SPDX expression, else trove classifier, else the
    first line of the License field when it looks like a name."""
    m = dist.metadata
    if norm(m["Name"]) in KNOWN:
        return KNOWN[norm(m["Name"])]
    lic = (m.get("License-Expression") or "").strip()
    if lic:
        return lic
    cls = [c.split("::")[-1].strip() for c in (m.get_all("Classifier") or []) if c.startswith("License ::")]
    if cls:
        return ", ".join(cls)
    first = (m.get("License") or "").strip().splitlines()
    if first and len(first[0]) < 40 and not re.search(r"copyright|=|agreement", first[0], re.I):
        return first[0]
    return "see licence files"


def homepage(dist):
    m = dist.metadata
    if m.get("Home-page"):
        return m["Home-page"]
    for u in m.get_all("Project-URL") or []:
        label, _, url = u.partition(",")
        if label.strip().lower() in ("homepage", "home", "source", "source code", "repository"):
            return url.strip()
    return ""


def main(out):
    if os.path.exists(out):
        shutil.rmtree(out)
    lic_dir = os.path.join(out, "licenses")
    os.makedirs(lic_dir)
    dists = runtime_closure(TOP)
    rows = []
    for key in sorted(dists):
        d = dists[key]
        name, ver = d.metadata["Name"], d.version
        copied = 0
        for f in d.files or []:
            if LICENSE_NAME.search(os.path.basename(str(f))):
                src = d.locate_file(f)
                if os.path.isfile(src):
                    rel = str(f).split(".dist-info/", 1)[-1]
                    dst = os.path.join(lic_dir, f"{name}-{ver}", rel)
                    os.makedirs(os.path.dirname(dst), exist_ok=True)
                    shutil.copyfile(src, dst)
                    copied += 1
        if key in ("pyside6-essentials", "shiboken6") and not copied:
            dst = os.path.join(lic_dir, f"{name}-{ver}")
            os.makedirs(dst, exist_ok=True)
            for t in ("lgpl-3.0.txt", "gpl-3.0.txt"):
                shutil.copyfile(os.path.join(HERE, "licenses", t), os.path.join(dst, t))
        rows.append((name, ver, licence_of(d), homepage(d)))
    # Python itself
    py = f"{sys.version_info.major}.{sys.version_info.minor}"
    for cand in (os.path.join(sys.base_prefix, "lib", f"python{py}", "LICENSE.txt"),
                 os.path.join(sys.base_prefix, "LICENSE.txt"), os.path.join(sys.base_prefix, "Lib", "LICENSE.txt")):
        if os.path.isfile(cand):
            os.makedirs(os.path.join(lic_dir, f"Python-{sys.version.split()[0]}"), exist_ok=True)
            shutil.copyfile(cand, os.path.join(lic_dir, f"Python-{sys.version.split()[0]}", "LICENSE.txt"))
            break
    rows.append(("Python", sys.version.split()[0], "PSF-2.0", "https://www.python.org"))
    for t in ("lgpl-3.0.txt", "gpl-3.0.txt"):
        shutil.copyfile(os.path.join(HERE, "licenses", t), os.path.join(out, t))

    import PySide6
    from PySide6.QtCore import qVersion
    qv, pv = qVersion(), PySide6.__version__
    mm = ".".join(qv.split(".")[:2])
    src = [f"https://download.qt.io/archive/qt/{mm}/{qv}/submodules/{m}-everywhere-src-{qv}.tar.xz" for m in QT_MODULES]
    src.append(f"https://download.qt.io/official_releases/QtForPython/pyside6/PySide6-{pv}-src/"
               f"pyside-setup-everywhere-src-{pv}.tar.xz")
    with open(os.path.join(out, "QT-SOURCE.txt"), "w", encoding="utf-8") as f:
        f.write(f"""Qt {qv} and Qt for Python (PySide6, Shiboken6) {pv} - corresponding source
=====================================================================

This application uses the Qt libraries (Qt Core, Qt Gui, Qt Widgets, Qt Svg and
their platform, style, icon-engine and image-format plug-ins) and Qt for Python
under the GNU Lesser General Public License version 3 (LGPLv3). The Qt libraries
are not modified. Copies of the GNU LGPLv3 and GNU GPLv3 are in lgpl-3.0.txt and
gpl-3.0.txt next to this file.

Qt is Copyright (C) The Qt Company Ltd. and other contributors.

The complete corresponding source of the Qt parts contained in this package is
attached to the same GitHub release as this package and is also available from
the Qt Project:

""")
        f.write("\n".join("  " + u for u in src) + "\n")
        f.write("""
Replacing the Qt libraries (relinking): the Qt libraries are separate shared
libraries inside the package (macOS: AutoDisloc2.app/Contents/Frameworks/PySide6/Qt/lib,
Windows: AutoDisloc2/_internal/PySide6). They can be replaced by
interface-compatible builds of the same Qt version. Alternatively, run the
program from its source code (MIT licence) with any PySide6 installation:
pip install -r requirements.txt ; python AutoDisloc2.py
""")
    with open(os.path.join(out, "QT-SOURCE-URLS.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(src) + "\n")

    w = max(len(r[0]) for r in rows)
    with open(os.path.join(out, "THIRD-PARTY-NOTICES.txt"), "w", encoding="utf-8") as f:
        f.write("AutoDisloc 2 - third-party software contained in this package\n")
        f.write("=" * 62 + "\n\n")
        f.write("AutoDisloc itself is licensed under the MIT licence (LICENSE). The packaged\n"
                "application also contains the following components, each under its own\n"
                "licence. Their licence texts are in the folder 'licenses'.\n\n")
        for name, ver, lic, url in rows:
            f.write(f"{name:<{w}}  {ver:<12} {lic}\n{'':<{w}}  {url}\n")
        f.write("\nQt / PySide6 / Shiboken6: used under the GNU LGPLv3, see QT-SOURCE.txt,\n"
                "lgpl-3.0.txt and gpl-3.0.txt.\n"
                "The application was packaged with PyInstaller, whose bootloader is distributed\n"
                "under the GPL with an exception that permits any licence for the packaged program.\n")
    print(f"{len(rows)} components -> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "build", "third_party")))
