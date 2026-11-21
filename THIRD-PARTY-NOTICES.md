# Third-party software

AutoDisloc is licensed under the [MIT licence](LICENSE). It uses the following
open-source components. **This repository does not contain them**: when you run
AutoDisloc from source, `pip` installs them under their own licences.

The **packaged applications** (macOS `.app`, Windows `.exe` on the Releases page)
contain these components. Each package therefore ships, in its `third_party`
folder, the licence texts of every bundled component (`licenses/`), the list of
components with their versions (`THIRD-PARTY-NOTICES.txt`), copies of the GNU GPL
and LGPL, and the Qt source-code information (`QT-SOURCE.txt`). The folder is
created by `packaging/collect_licenses.py` during packaging.

| Component | Licence | Use |
|---|---|---|
| [Qt](https://www.qt.io) 6 (Qt Core, Gui, Widgets, Svg) | LGPL-3.0 | graphical user interface |
| [Qt for Python](https://pyside.org) (PySide6-Essentials, Shiboken6) | LGPL-3.0 | Python binding of Qt |
| [NumPy](https://numpy.org) | BSD-3-Clause (and bundled components) | numerics |
| [SciPy](https://scipy.org) | BSD-3-Clause (and bundled components) | fitting, integration |
| [pandas](https://pandas.pydata.org) | BSD-3-Clause | tables |
| [matplotlib](https://matplotlib.org) | Matplotlib License (PSF-based); fonts DejaVu, STIX (OFL) | figures |
| [openpyxl](https://openpyxl.readthedocs.io) | MIT | Excel reports |
| [Pillow](https://python-pillow.org) | MIT-CMU | images |
| [Python](https://www.python.org) (packaged applications only) | PSF-2.0 | interpreter |
| [PyInstaller](https://pyinstaller.org) bootloader (packaged applications only) | GPL-2.0-or-later with bootloader exception (any licence for the packaged program) | packaging |

Further dependencies of these packages (contourpy, cycler, fonttools, kiwisolver,
packaging, pyparsing, python-dateutil, tzdata, et_xmlfile) are listed with their
licences in the `THIRD-PARTY-NOTICES.txt` of each package.

## Qt and the GNU LGPLv3

AutoDisloc uses Qt through PySide6 under the GNU Lesser General Public License
version 3. Qt is Copyright © The Qt Company Ltd. and other contributors.

- The Qt libraries are used unmodified and as separate shared libraries, so they
  can be replaced by interface-compatible builds (macOS:
  `AutoDisloc2.app/Contents/Frameworks/PySide6/Qt/lib`; Windows:
  `AutoDisloc2/_internal/PySide6`). The complete source of AutoDisloc is in this
  repository, so the program can also be run from source with any PySide6
  installation (`pip install -r requirements.txt`, `python AutoDisloc2.py`).
- Only Qt parts available under the LGPLv3 are packaged (Qt Base, Qt SVG, Qt Image
  Formats; see the allow-list in `packaging/AutoDisloc2.spec`).
- The corresponding source of the packaged Qt and PySide6 versions
  (`qtbase`, `qtsvg`, `qtimageformats`, `pyside-setup`) is attached to every GitHub
  release that contains packaged applications, and is also available from
  <https://download.qt.io>.
- Copies of the GNU GPL v3 and LGPL v3 are in `packaging/licenses/` and in the
  `third_party` folder of every package.
