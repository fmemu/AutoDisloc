# SPDX-License-Identifier: MIT
# AutoDisloc 2 - Copyright (c) 2026 Firat Memu
# PyInstaller spec - build on the target OS:
#   macOS:   packaging/build_mac.sh
#   Windows: packaging\build_windows.bat
#
# Licences: the third-party licence texts, the Qt source information and the
# GNU GPL/LGPL texts are collected by packaging/collect_licenses.py and shipped
# in the folder "third_party". Only the Qt parts that the program uses are
# packaged (allow-list below), all of them available under the LGPLv3.
import os
import re
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(SPECPATH, ".."))
THIRD = os.environ.get("AUTODISLOC_THIRD_DIR") or os.path.join(ROOT, "build", "third_party")
subprocess.run([sys.executable, os.path.join(ROOT, "packaging", "collect_licenses.py"), THIRD], check=True)

datas = [
    (os.path.join(ROOT, "autodisloc", "data", "instrument_corundum_example.json"), os.path.join("autodisloc", "data")),
    (os.path.join(ROOT, "assets", "icon.png"), "assets"),
    (os.path.join(ROOT, "LICENSE"), "."),
    (THIRD, "third_party"),
]
for lang in ("EN", "TR"):
    for sub, stem in (("whitepaper", "AutoDisloc2_Whitepaper"), ("manual", "AutoDisloc2_Manual")):
        f = os.path.join(ROOT, "docs", sub, f"{stem}_{lang}.pdf")
        if os.path.exists(f):
            datas.append((f, os.path.join("docs", sub)))

a = Analysis([os.path.join(ROOT, "AutoDisloc2.py")], pathex=[ROOT], datas=datas,
             hiddenimports=["matplotlib.backends.backend_qtagg", "matplotlib.backends.backend_agg",
                            "matplotlib.backends.backend_pdf", "matplotlib.backends.backend_svg",
                            "matplotlib.backends.backend_ps", "openpyxl", "PySide6.QtSvg"],
             excludes=["PyQt5", "PyQt6", "PySide2", "tkinter", "IPython", "notebook", "streamlit",
                       "PySide6.QtWebEngineCore", "PySide6.QtWebEngineWidgets", "PySide6.QtQml",
                       "PySide6.QtQuick", "PySide6.QtQuickWidgets", "PySide6.QtPdf", "PySide6.QtDesigner",
                       "PySide6.QtHelp", "PySide6.QtUiTools", "torch", "tensorflow"],
             noarchive=False)

# --- Qt allow-list -----------------------------------------------------------
QT_LIBS = {"Core", "Gui", "Widgets", "Svg", "SvgWidgets", "DBus", "Network", "OpenGL", "PrintSupport"}
QT_PLUGIN_DIRS = {"platforms", "styles", "imageformats", "iconengines"}
QT_PLUGIN_DROP = re.compile(r"(qpdf|lottie|virtualkeyboard)", re.I)
QT_LIB = re.compile(r"(?:^|[/\\])(?:lib)?Qt6?([A-Z][A-Za-z0-9]*?)(?:\.framework[/\\]|\.dll$|\.abi3\.so$|\.pyd$|\.so(?:\.\d+)*$|$)")


def _keep(entry):
    dest = entry[0].replace("\\", "/")
    if "PySide6/" not in dest and not dest.startswith(("Qt", "lib/Qt", "PySide6")):
        return True
    if "/qml/" in dest or dest.endswith("/qml"):
        return False
    m = re.search(r"/plugins/([^/]+)/", dest)
    if m:
        return m.group(1) in QT_PLUGIN_DIRS and not QT_PLUGIN_DROP.search(dest)
    m = QT_LIB.search(dest)
    if m and m.group(1):
        return m.group(1) in QT_LIBS
    return True


_before = len(a.binaries) + len(a.datas)
a.binaries = [e for e in a.binaries if _keep(e)]
a.datas = [e for e in a.datas if _keep(e)]
print(f"Qt allow-list removed {_before - len(a.binaries) - len(a.datas)} entries")

pyz = PYZ(a.pure)
icon_win = os.path.join(ROOT, "assets", "icon.ico")
icon_mac = os.path.join(ROOT, "assets", "icon.icns")
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name="AutoDisloc2", console=False,
          icon=icon_win if sys.platform.startswith("win") else icon_mac)
coll = COLLECT(exe, a.binaries, a.datas, name="AutoDisloc2")
if sys.platform == "darwin":
    app = BUNDLE(coll, name="AutoDisloc2.app", icon=icon_mac, bundle_identifier="com.firatmemu.autodisloc2",
                 info_plist={"NSHighResolutionCapable": True, "CFBundleShortVersionString": "2.0.0",
                             "NSHumanReadableCopyright": "© 2026 Fırat Memu, MIT License. "
                                                         "Uses Qt (LGPLv3), see third_party."})
