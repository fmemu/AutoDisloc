# SPDX-License-Identifier: MIT
# AutoDisloc 2 - Copyright (c) 2026 Firat Memu
"""Optional step-by-step assistant and the small dialogs shared with the main
window: measurement data (radiation, Ka2, goniometer radius), material
(titanium alloy, nominal lattice) and instrument standard (corundum, LaB6,
Si, CeO2 or another material).

All settings travel in one dict ("cfg", see MainWindow._cfg):
    files     [(path, name)]
    radiation None (from file) | anode name | (wl1, wl2, ratio)
    radius    None (from file) | mm
    ka2       None (from file) | False (present) | True (stripped)
    material  {"key", "a", "c", "ab", "beta", "refine"}
    inst, inst_path, zero, wp, mwh, fourier, M, mc
"""

import os

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QButtonGroup, QCheckBox, QComboBox,
                               QDialog, QDialogButtonBox, QDoubleSpinBox, QFileDialog, QFormLayout,
                               QGroupBox, QHBoxLayout, QHeaderView, QLabel, QListWidget, QListWidgetItem,
                               QPushButton, QRadioButton, QScrollArea, QSpinBox, QTableWidget,
                               QTableWidgetItem, QTextBrowser, QVBoxLayout, QWidget, QWizard, QWizardPage,
                               QFrame)

from . import materials, standards
from .i18n import tr
from .instrument import InstrumentModel, fit_instrument
from .io import ANODES, read_pattern

RAD_KEYS = [None] + list(ANODES) + ["custom"]
KA2_CHOICES = (None, False, True)        # automatic, present, stripped


def _spin(lo, hi, dec, val, step=None, special=None):
    s = QDoubleSpinBox()
    s.setRange(lo, hi)
    s.setDecimals(dec)
    s.setValue(val)
    s.setSingleStep(step or 10 ** -dec)
    if special:
        s.setSpecialValueText(special)
    return s


def _muted(text):
    lab = QLabel(text)
    lab.setWordWrap(True)
    lab.setObjectName("muted")
    lab.setTextFormat(Qt.RichText)
    return lab


def _ok_cancel(dlg):
    bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
    bb.button(QDialogButtonBox.Ok).setText(tr("dlg.ok"))
    bb.button(QDialogButtonBox.Cancel).setText(tr("wz.cancel"))
    bb.accepted.connect(dlg.accept)
    bb.rejected.connect(dlg.reject)
    return bb


def radiation_text(rad):
    if rad is None:
        return tr("gui.rad_file")
    if isinstance(rad, str):
        return tr("wz.rad_preset", a=rad)
    return tr("gui.rad_custom_set", wl1=rad[0])


def material_text(m):
    if m["key"] == "custom":
        return tr("gui.mat_custom_set", a=m["a"], c=m["c"])
    return materials.display_name(m["key"])


def material_cfg(key, refine=True):
    mt = materials.get(key)
    return {"key": mt.key, "a": mt.a, "c": mt.c, "ab": mt.a_beta, "beta": mt.beta, "refine": refine}


# ---------------------------------------------------------------- forms
class RadiationForm(QWidget):
    """Radiation preset or custom wavelengths, Ka2 handling, goniometer radius."""

    def __init__(self, rad=None, ka2=None, radius=None, with_extra=True):
        super().__init__()
        fl = QFormLayout(self)
        fl.setContentsMargins(0, 0, 0, 0)
        self.combo = QComboBox()
        self.combo.addItems([tr("gui.rad_file")] + [tr("wz.rad_preset", a=k) for k in ANODES]
                            + [tr("gui.rad_custom")])
        self.combo.setToolTip(tr("gui.rad_tip"))
        fl.addRow(tr("gui.radiation"), self.combo)
        self.wl1 = _spin(0.3, 3.0, 6, 1.540598)
        self.wl2 = _spin(0.3, 3.0, 6, 1.544426)
        self.ratio = _spin(0.0, 1.0, 3, 0.5, 0.01)
        row = QHBoxLayout()
        for lab, w in (("λ₁", self.wl1), ("λ₂", self.wl2), ("Kα2/Kα1", self.ratio)):
            row.addWidget(QLabel(lab))
            row.addWidget(w)
        fl.addRow("", row)
        self.ka2 = self.radius = None
        if with_extra:
            self.ka2 = QComboBox()
            self.ka2.addItems([tr("gui.ka2_auto"), tr("gui.ka2_present"), tr("gui.ka2_stripped")])
            self.ka2.setToolTip(tr("gui.ka2_tip"))
            self.ka2.setCurrentIndex(KA2_CHOICES.index(ka2))
            fl.addRow(tr("gui.ka2"), self.ka2)
            self.radius = _spin(0, 1000, 1, radius or 0, 1.0, tr("gui.radius_file"))
            self.radius.setSuffix(" mm")
            self.radius.setToolTip(tr("gui.radius_tip"))
            fl.addRow(tr("gui.radius"), self.radius)
        self.combo.currentIndexChanged.connect(self._sync)
        self.set_radiation(rad)

    def set_radiation(self, rad):
        if rad is None or isinstance(rad, str):
            self.combo.setCurrentIndex(RAD_KEYS.index(rad))
        else:
            self.combo.setCurrentIndex(len(RAD_KEYS) - 1)
            self.wl1.setValue(rad[0])
            self.wl2.setValue(rad[1])
            self.ratio.setValue(rad[2] if len(rad) > 2 else 0.5)
        self._sync()

    def _sync(self):
        key = RAD_KEYS[self.combo.currentIndex()]
        custom = key == "custom"
        for w in (self.wl1, self.wl2, self.ratio):
            w.setEnabled(custom)
        if key in ANODES:
            self.wl1.setValue(ANODES[key][0])
            self.wl2.setValue(ANODES[key][1])

    def radiation(self):
        key = RAD_KEYS[self.combo.currentIndex()]
        if key == "custom":
            return (self.wl1.value(), self.wl2.value(), self.ratio.value())
        return key

    def ka2_value(self):
        return KA2_CHOICES[self.ka2.currentIndex()] if self.ka2 else None

    def radius_value(self):
        return (self.radius.value() or None) if self.radius else None


class MaterialForm(QWidget):
    def __init__(self, m):
        super().__init__()
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        fl = QFormLayout()
        self.preset = QComboBox()
        self.preset.addItems([materials.display_name(k) for k in materials.MATERIAL_KEYS])
        fl.addRow(tr("mat.preset"), self.preset)
        self.a = _spin(2.5, 3.5, 4, m["a"], 0.001)
        self.c = _spin(4.0, 5.5, 4, m["c"], 0.001)
        self.ab = _spin(2.9, 3.6, 4, m["ab"], 0.001)
        for lab, w in (("mat.a", self.a), ("mat.c", self.c), ("mat.ab", self.ab)):
            fl.addRow(tr(lab), w)
        self.beta = QComboBox()
        self.beta.addItems([tr("mat.beta_auto"), tr("mat.beta_yes"), tr("mat.beta_no")])
        fl.addRow(tr("mat.beta"), self.beta)
        lay.addLayout(fl)
        self.refine = QCheckBox(tr("mat.refine"))
        lay.addWidget(self.refine)
        self.source = _muted("")
        lay.addWidget(self.source)
        lay.addWidget(_muted(tr("mat.note")))
        self._busy = False
        self.set(m)
        self.preset.currentIndexChanged.connect(self._preset)
        for w in (self.a, self.c, self.ab):
            w.valueChanged.connect(self._edited)

    def set(self, m):
        self._busy = True
        self.preset.setCurrentIndex(materials.MATERIAL_KEYS.index(m["key"]))
        self.a.setValue(m["a"])
        self.c.setValue(m["c"])
        self.ab.setValue(m["ab"])
        self.beta.setCurrentIndex(("auto", "yes", "no").index(m["beta"]))
        self.refine.setChecked(m.get("refine", True))
        self.source.setText(tr("std.source", s=materials.display_source(m["key"])))
        self._busy = False

    def _preset(self, i):
        if self._busy:
            return
        key = materials.MATERIAL_KEYS[i]
        if key == "custom":
            self.source.setText(tr("std.source", s=materials.display_source(key)))
            return
        self.set(material_cfg(key, self.refine.isChecked()))

    def _edited(self):
        if self._busy:
            return
        mt = materials.get(materials.MATERIAL_KEYS[self.preset.currentIndex()])
        if (abs(self.a.value() - mt.a) > 5e-5 or abs(self.c.value() - mt.c) > 5e-5
                or abs(self.ab.value() - mt.a_beta) > 5e-5):
            self._busy = True
            self.preset.setCurrentIndex(materials.MATERIAL_KEYS.index("custom"))
            self.source.setText(tr("std.source", s=materials.display_source("custom")))
            self._busy = False

    def get(self):
        return {"key": materials.MATERIAL_KEYS[self.preset.currentIndex()], "a": self.a.value(),
                "c": self.c.value(), "ab": self.ab.value(),
                "beta": ("auto", "yes", "no")[self.beta.currentIndex()], "refine": self.refine.isChecked()}


class StandardForm(QWidget):
    """Standard material with its (editable) lattice parameters."""

    def __init__(self, key="corundum"):
        super().__init__()
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        fl = QFormLayout()
        self.combo = QComboBox()
        self.combo.addItems([standards.display_name(k) for k in standards.STANDARD_KEYS])
        fl.addRow(tr("std.material"), self.combo)
        self.a = _spin(1.0, 30.0, 6, 4.7588, 0.0001)
        self.c = _spin(1.0, 60.0, 6, 12.991, 0.0001)
        self.a_lab, self.c_lab = QLabel("a (Å)"), QLabel("c (Å)")
        fl.addRow(self.a_lab, self.a)
        fl.addRow(self.c_lab, self.c)
        self.degree = QSpinBox()
        self.degree.setRange(1, 2)
        self.degree.setValue(1)
        fl.addRow(tr("std.degree"), self.degree)
        lay.addLayout(fl)
        self.source = _muted("")
        lay.addWidget(self.source)
        lay.addWidget(_muted(tr("std.cert_note")))
        self.combo.currentIndexChanged.connect(self._sync)
        self.combo.setCurrentIndex(standards.STANDARD_KEYS.index(key))
        self._sync()

    def _sync(self):
        std = standards.get(self.key())
        known = bool(std.system)
        hexa = std.system == "hexagonal"
        for w in (self.a, self.a_lab):
            w.setVisible(known)
        for w in (self.c, self.c_lab):
            w.setVisible(hexa)
        if known:
            self.a.setValue(std.a)
        if hexa:
            self.c.setValue(std.c)
        self.source.setText(tr("std.source", s=standards.display_source(std.key)) if known else tr("std.other_note"))

    def key(self):
        return standards.STANDARD_KEYS[self.combo.currentIndex()]

    def lattice(self):
        std = standards.get(self.key())
        if not std.system:
            return {}
        return {"a": self.a.value(), "c": self.c.value() if std.system == "hexagonal" else float("nan")}


# ---------------------------------------------------------------- dialogs
class RadiationDialog(QDialog):
    def __init__(self, parent, rad):
        super().__init__(parent)
        self.setWindowTitle(tr("dlg.rad_title"))
        lay = QVBoxLayout(self)
        self.form = RadiationForm(rad if not isinstance(rad, str) else ANODES[rad] + (0.5,), with_extra=False)
        self.form.combo.setCurrentIndex(len(RAD_KEYS) - 1)
        lay.addWidget(self.form)
        lay.addWidget(_ok_cancel(self))

    def value(self):
        return self.form.radiation()


class MaterialDialog(QDialog):
    def __init__(self, parent, m):
        super().__init__(parent)
        self.setWindowTitle(tr("dlg.mat_title"))
        self.setMinimumWidth(460)
        lay = QVBoxLayout(self)
        self.form = MaterialForm(m)
        lay.addWidget(self.form)
        lay.addWidget(_ok_cancel(self))

    def value(self):
        return self.form.get()


class StandardDialog(QDialog):
    """Standard pattern file and standard material for building an instrument model."""

    def __init__(self, parent, start_dir, key="corundum"):
        super().__init__(parent)
        self.setWindowTitle(tr("dlg.std_title"))
        self.setMinimumWidth(480)
        self.start_dir = start_dir
        self.path = ""
        lay = QVBoxLayout(self)
        row = QHBoxLayout()
        self.file_lab = QLabel(tr("dlg.none"))
        self.file_lab.setWordWrap(True)
        b = QPushButton(tr("dlg.browse"))
        b.clicked.connect(self._browse)
        row.addWidget(QLabel(tr("dlg.std_file") + ":"))
        row.addWidget(self.file_lab, 1)
        row.addWidget(b)
        lay.addLayout(row)
        self.form = StandardForm(key)
        lay.addWidget(self.form)
        self.bb = _ok_cancel(self)
        self.bb.button(QDialogButtonBox.Ok).setEnabled(False)
        lay.addWidget(self.bb)

    def _browse(self):
        p, _ = QFileDialog.getOpenFileName(self, tr("gui.dlg_std"), self.start_dir, tr("gui.file_filter"))
        if p:
            self.path = p
            self.file_lab.setText(os.path.basename(p))
            self.bb.button(QDialogButtonBox.Ok).setEnabled(True)


def show_file_info(parent, path, rad=None, radius=None, ka2=None):
    """Message box with the measurement metadata of one file."""
    from PySide6.QtWidgets import QMessageBox
    from .io import describe
    try:
        p = read_pattern(path, ka2_stripped=ka2, radiation=rad, radius_mm=radius)
        rows = describe(p)
        user = {"wavelength": rad is not None, "ka2": ka2 is not None, "radius": radius is not None}
        keymap = {"anode": "wavelength", "wl1": "wavelength", "wl2": "wavelength", "ka2": "ka2", "radius": "radius"}
        html = "<table cellspacing=4>"
        for k, v, ok in rows:
            src = tr("meta.user") if user.get(keymap.get(k, ""), False) else (
                tr("meta.file") if ok else "<b style='color:#c0392b'>" + tr("meta.assumed") + "</b>")
            html += f"<tr><td>{tr('meta.' + k)}</td><td><b>{v}</b></td><td>{src}</td></tr>"
        html += "</table>"
    except Exception as e:  # pragma: no cover
        html = tr("wz.read_error", e=e)
    box = QMessageBox(parent)
    box.setWindowTitle(tr("meta.title", f=os.path.basename(path)))
    box.setTextFormat(Qt.RichText)
    box.setText(html)
    box.exec()


# ---------------------------------------------------------------- wizard pages
class _Page(QWizardPage):
    def __init__(self, title, sub):
        super().__init__()
        self.setTitle(title)
        self.setSubTitle(sub)
        self.lay = QVBoxLayout(self)

    @property
    def cfg(self):
        return self.wizard().cfg


class IntroPage(_Page):
    def __init__(self, offer):
        super().__init__(tr("wz.intro_t"), "")
        t = QLabel(tr("wz.intro"))
        t.setWordWrap(True)
        t.setTextFormat(Qt.RichText)
        self.lay.addWidget(t)
        self.lay.addStretch(1)
        self.offer = QCheckBox(tr("wz.offer_check"))
        self.offer.setChecked(offer)
        self.lay.addWidget(self.offer)


class DataPage(_Page):
    COLS = ("wz.col_file", "meta.format", "meta.wl1", "meta.ka2", "meta.radius", "meta.source")

    def __init__(self):
        super().__init__(tr("wz.data_t"), tr("wz.data_s"))
        self._cache = {}
        row = QHBoxLayout()
        self.list = QListWidget()
        self.list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.list.setMaximumHeight(110)
        row.addWidget(self.list, 1)
        col = QVBoxLayout()
        for key, fn in (("gui.add", self._add), ("gui.remove", self._remove)):
            b = QPushButton(tr(key))
            b.clicked.connect(fn)
            col.addWidget(b)
        col.addStretch(1)
        row.addLayout(col)
        self.lay.addLayout(row)
        self.table = QTableWidget(0, len(self.COLS))
        self.table.setHorizontalHeaderLabels([tr(k) for k in self.COLS])
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.lay.addWidget(self.table, 1)
        g = QGroupBox(tr("wz.override"))
        gl = QVBoxLayout(g)
        self.form = RadiationForm()
        gl.addWidget(self.form)
        self.lay.addWidget(g)
        self.form.combo.currentIndexChanged.connect(self._refresh)
        for w in (self.form.wl1, self.form.wl2, self.form.ratio, self.form.radius):
            w.valueChanged.connect(self._refresh)
        self.form.ka2.currentIndexChanged.connect(self._refresh)

    def initializePage(self):
        c = self.cfg
        self.list.clear()
        for p, name in c["files"]:
            self._item(p, name)
        self.form.set_radiation(c["radiation"])
        self.form.ka2.setCurrentIndex(KA2_CHOICES.index(c["ka2"]))
        self.form.radius.setValue(c["radius"] or 0)
        self._refresh()

    def _item(self, p, name):
        it = QListWidgetItem(name)
        it.setData(Qt.UserRole, p)
        it.setToolTip(p)
        self.list.addItem(it)

    def _add(self):
        w = self.wizard()
        ps, _ = QFileDialog.getOpenFileNames(self, tr("gui.dlg_samples"), w.start_dir, tr("gui.file_filter"))
        for p in ps:
            self._item(p, os.path.splitext(os.path.basename(p))[0])
        if ps:
            w.start_dir = os.path.dirname(ps[0])
        self._refresh()

    def _remove(self):
        for it in self.list.selectedItems():
            self.list.takeItem(self.list.row(it))
        self._refresh()

    def files(self):
        return [(self.list.item(i).data(Qt.UserRole), self.list.item(i).text()) for i in range(self.list.count())]

    def _meta(self, path):
        if path not in self._cache:
            try:
                p = read_pattern(path)
                guess = ""
                if "wavelength" in p.assumed:
                    from . import ti64
                    name, n = ti64.best_anode(p)
                    if name and name != p.anode and n >= max(ti64.refine_nominal(p)[2] + 2, 4):
                        guess = name
                self._cache[path] = (p.fmt, p.wl1, p.wl2, p.ka2_ratio, p.radius_mm, list(p.assumed), None, guess)
            except Exception as e:
                self._cache[path] = (None,) * 6 + (str(e), "")
        return self._cache[path]

    def _refresh(self, *_):
        rad, ka2, radius = self.form.radiation(), self.form.ka2_value(), self.form.radius_value()
        files = self.files()
        self.table.setRowCount(len(files))
        for i, (path, name) in enumerate(files):
            fmt, wl1, wl2, ratio, rr, assumed, err, guess = self._meta(path)
            if err:
                vals = [name, tr("wz.read_error", e=err), "", "", "", ""]
            else:
                src = []
                if rad is not None:
                    wl1, wl2 = (ANODES[rad] if isinstance(rad, str) else rad[:2])
                    if not isinstance(rad, str):
                        ratio = rad[2]
                    src.append("λ: " + tr("meta.user"))
                else:
                    src.append("λ: " + tr("meta.assumed" if "wavelength" in assumed else "meta.file")
                               + (" (" + tr("wz.guess", anode=guess) + ")" if guess else ""))
                if ka2 is not None:
                    ratio = 0.0 if ka2 else (ratio or 0.5)
                if radius:
                    rr = radius
                    src.append("R: " + tr("meta.user"))
                else:
                    src.append("R: " + tr("meta.assumed" if "radius" in assumed else "meta.file"))
                ka2_txt = f"{ratio:.3f}" + (f" ({tr('ka2.stripped')})" if ratio == 0 else "")
                fmt = tr("meta.xy") if fmt == "2-column text" else fmt
                vals = [name, fmt, f"{wl1:.6f} Å", ka2_txt, f"{rr:.1f} mm", " · ".join(src)]
            for j, v in enumerate(vals):
                it = QTableWidgetItem(v)
                if j == 5 and tr("meta.assumed") in v:
                    it.setForeground(Qt.red)
                self.table.setItem(i, j, it)
        self.completeChanged.emit()

    def isComplete(self):
        return self.list.count() > 0

    def validatePage(self):
        c = self.cfg
        c["files"] = self.files()
        c["radiation"] = self.form.radiation()
        c["ka2"] = self.form.ka2_value()
        c["radius"] = self.form.radius_value()
        return True


class MaterialPage(_Page):
    def __init__(self):
        super().__init__(tr("wz.mat_t"), tr("wz.mat_s"))
        self.form = None

    def initializePage(self):
        if self.form is None:
            self.form = MaterialForm(self.cfg["material"])
            self.lay.addWidget(self.form)
            self.lay.addStretch(1)
        else:
            self.form.set(self.cfg["material"])

    def validatePage(self):
        self.cfg["material"] = self.form.get()
        return True


class InstrumentPage(_Page):
    def __init__(self):
        super().__init__(tr("wz.inst_t"), tr("wz.inst_s"))
        outer = self.lay
        area = QScrollArea()
        area.setWidgetResizable(True)
        area.setFrameShape(QFrame.NoFrame)
        body = QWidget()
        area.setWidget(body)
        outer.addWidget(area)
        self.lay = QVBoxLayout(body)
        self.loaded = self.built = None
        self.loaded_path = self.std_path = ""
        self.group = QButtonGroup(self)
        self.r_keep = QRadioButton(tr("wz.inst_keep"))
        self.keep_lab = _muted("")
        self.r_load = QRadioButton(tr("wz.inst_load"))
        self.load_lab = _muted(tr("dlg.none"))
        b_load = QPushButton(tr("dlg.browse"))
        b_load.clicked.connect(self._browse_model)
        self.r_build = QRadioButton(tr("wz.inst_build"))
        for i, r in enumerate((self.r_keep, self.r_load, self.r_build)):
            self.group.addButton(r, i)
        self.lay.addWidget(self.r_keep)
        self.lay.addWidget(self.keep_lab)
        row = QHBoxLayout()
        row.addWidget(self.r_load)
        row.addStretch(1)
        row.addWidget(b_load)
        self.lay.addLayout(row)
        self.lay.addWidget(self.load_lab)
        self.lay.addWidget(self.r_build)
        self.build_box = QWidget()
        bl = QVBoxLayout(self.build_box)
        bl.setContentsMargins(22, 0, 0, 0)
        row = QHBoxLayout()
        self.std_lab = QLabel(tr("dlg.none"))
        b = QPushButton(tr("dlg.browse"))
        b.clicked.connect(self._browse_std)
        row.addWidget(QLabel(tr("dlg.std_file") + ":"))
        row.addWidget(self.std_lab, 1)
        row.addWidget(b)
        bl.addLayout(row)
        self.std_form = StandardForm()
        bl.addWidget(self.std_form)
        row = QHBoxLayout()
        self.fit_btn = QPushButton(tr("wz.fit"))
        self.fit_btn.clicked.connect(self._fit)
        self.save_btn = QPushButton(tr("wz.save"))
        self.save_btn.clicked.connect(self._save)
        self.save_btn.setEnabled(False)
        row.addWidget(self.fit_btn)
        row.addWidget(self.save_btn)
        row.addStretch(1)
        bl.addLayout(row)
        self.lay.addWidget(self.build_box)
        self.result = _muted("")
        self.lay.addWidget(self.result)
        self.zero = QCheckBox(tr("wz.zero_apply"))
        self.lay.addWidget(self.zero)
        self.lay.addStretch(1)
        self.group.idToggled.connect(self._sync)

    def initializePage(self):
        c = self.cfg
        inst = c["inst"]
        if inst is not None:
            self.keep_lab.setText(self._describe(inst, c["inst_path"]))
            self.r_keep.setEnabled(True)
            if self.group.checkedId() < 0:
                self.r_keep.setChecked(True)
        else:
            self.keep_lab.setText(tr("wz.no_model"))
            self.r_keep.setEnabled(False)
            if self.group.checkedId() <= 0:
                self.r_build.setChecked(True)
        self.zero.setChecked(c["zero"])
        self._sync()

    def _describe(self, inst, path):
        head = "<b>" + (os.path.basename(path or "") or inst.name) + "</b>"
        lines = inst.describe() + [tr("wz.fit_ok", n=len((inst.points or {}).get("K", [])), k0=inst.k_range[0],
                                         k1=inst.k_range[1])]
        return head + "<br>" + " · ".join(lines) + self._wl_check(inst)

    def _wl_check(self, inst):
        wl_std = inst.wavelength[0] if inst.wavelength else None
        if wl_std is None:
            return ""
        c = self.cfg
        rad = c["radiation"]
        wls = []
        if rad is not None:
            wls = [ANODES[rad][0] if isinstance(rad, str) else rad[0]]
        else:
            for p, _ in c["files"]:
                try:
                    wls.append(read_pattern(p).wl1)
                except Exception:
                    pass
        bad = [w for w in wls if abs(w - wl_std) > 2e-3]
        if bad:
            return "<br><b style='color:#c0392b'>" + tr("w.wl_mismatch", wl=bad[0], wl_std=wl_std) + "</b>"
        r_std = getattr(inst, "radius_mm", None)
        if r_std and not c["radius"]:
            for p, _ in c["files"]:
                try:
                    pat = read_pattern(p)
                except Exception:
                    continue
                if "radius" not in pat.assumed and abs(pat.radius_mm - r_std) > 1.0:
                    return ("<br><b style='color:#c0392b'>" + tr("w.radius_mismatch", r=pat.radius_mm, r_std=r_std)
                            + "</b>")
        return "<br>" + tr("wz.wl_ok") if wls else ""

    def current(self):
        i = self.group.checkedId()
        if i == 0:
            return self.cfg["inst"], self.cfg["inst_path"]
        if i == 1:
            return self.loaded, self.loaded_path
        if i == 2:
            return self.built, self.std_path
        return None, ""

    def _sync(self, *_):
        self.build_box.setEnabled(self.group.checkedId() == 2)
        inst, _ = self.current()
        self.zero.setEnabled(inst is not None and getattr(inst, "n_indexed", None) is not None)
        self.completeChanged.emit()

    def _browse_model(self):
        w = self.wizard()
        p, _ = QFileDialog.getOpenFileName(self, tr("gui.dlg_inst"), w.start_dir, "JSON (*.json)")
        if not p:
            return
        try:
            self.loaded, self.loaded_path = InstrumentModel.load(p), p
        except Exception as e:
            self.load_lab.setText(tr("wz.read_error", e=e))
            return
        self.load_lab.setText(self._describe(self.loaded, p))
        self.r_load.setChecked(True)
        self._sync()

    def _browse_std(self):
        w = self.wizard()
        p, _ = QFileDialog.getOpenFileName(self, tr("gui.dlg_std"), w.start_dir, tr("gui.file_filter"))
        if p:
            self.std_path = p
            self.std_lab.setText(os.path.basename(p))
            self.built = None
            self.save_btn.setEnabled(False)
            self.result.setText("")
            self._sync()

    def _fit(self):
        if not self.std_path:
            self._browse_std()
            if not self.std_path:
                return
        c = self.cfg
        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            inst = fit_instrument(self.std_path, degree=self.std_form.degree.value(), ka2_stripped=c["ka2"],
                                  standard=self.std_form.key(), lattice=self.std_form.lattice(),
                                  radiation=c["radiation"], radius_mm=c["radius"],
                                  name=os.path.basename(self.std_path))
        except Exception as e:
            QApplication.restoreOverrideCursor()
            self.result.setText("<b style='color:#c0392b'>" + tr("gui.std_failed", e=e).replace("\n", "<br>") + "</b>")
            self.built = None
            self._sync()
            return
        QApplication.restoreOverrideCursor()
        self.built = inst
        warn = "".join("<br>• " + str(m) for m in getattr(inst, "fit_warnings", []))
        self.result.setText(self._describe(inst, self.std_path) + warn)
        self.save_btn.setEnabled(True)
        self._sync()

    def _save(self):
        if self.built is None:
            return
        out, _ = QFileDialog.getSaveFileName(self, tr("gui.dlg_save_inst"),
                                             os.path.splitext(self.std_path)[0] + tr("gui.inst_suffix"),
                                             "JSON (*.json)")
        if out:
            self.built.save(out)
            self.std_path = out
            self.wizard().saved_instrument = out

    def isComplete(self):
        return self.current()[0] is not None

    def validatePage(self):
        inst, path = self.current()
        self.cfg["inst"], self.cfg["inst_path"] = inst, path
        self.cfg["zero"] = self.zero.isChecked() and self.zero.isEnabled()
        return True


class OptionsPage(_Page):
    def __init__(self):
        super().__init__(tr("wz.opt_t"), tr("wz.opt_s"))
        fl = QFormLayout()
        self.wp = QCheckBox(tr("gui.opt_wp"))
        fl.addRow(self.wp)
        self.mwh = QComboBox()
        self.mwh.addItems([tr("gui.mwh_con"), tr("gui.mwh_free")])
        fl.addRow("mWH", self.mwh)
        self.fourier = QComboBox()
        self.fourier.addItems([tr("gui.four_voigt"), tr("gui.four_eq13")])
        fl.addRow("Voigt-mWA", self.fourier)
        self.M = _spin(0.3, 10, 2, 2.64, 0.05)
        self.M.setToolTip(tr("gui.ref_M_tip"))
        lab_M = QLabel(tr("gui.ref_M"))
        lab_M.setToolTip(tr("gui.ref_M_tip"))
        fl.addRow(lab_M, self.M)
        self.mc = QSpinBox()
        self.mc.setRange(0, 1000)
        fl.addRow(tr("gui.mc"), self.mc)
        self.lay.addLayout(fl)
        self.lay.addWidget(_muted(tr("gui.ref_M_tip")))
        self.lay.addWidget(_muted(tr("gui.note")))
        self.lay.addStretch(1)

    def initializePage(self):
        c = self.cfg
        self.wp.setChecked(c["wp"])
        self.mwh.setCurrentIndex(c["mwh"])
        self.fourier.setCurrentIndex(c["fourier"])
        self.M.setValue(c["M"])
        self.mc.setValue(c["mc"])

    def validatePage(self):
        c = self.cfg
        c.update(wp=self.wp.isChecked(), mwh=self.mwh.currentIndex(), fourier=self.fourier.currentIndex(),
                 M=self.M.value(), mc=self.mc.value())
        return True


class SummaryPage(_Page):
    def __init__(self):
        super().__init__(tr("wz.sum_t"), tr("wz.sum_s"))
        self.text = QTextBrowser()
        self.lay.addWidget(self.text)

    def initializePage(self):
        c = self.cfg
        yes = lambda v: tr("wz.yes") if v else tr("wz.no")
        m = c["material"]
        inst = c["inst"]
        ka2 = (tr("gui.ka2_auto"), tr("gui.ka2_present"), tr("gui.ka2_stripped"))[KA2_CHOICES.index(c["ka2"])]
        rows = [
            (tr("wz.files"), "<br>".join(n for _, n in c["files"])),
            (tr("gui.radiation"), radiation_text(c["radiation"])),
            (tr("gui.ka2"), ka2),
            (tr("gui.radius"), f"{c['radius']:.1f} mm" if c["radius"] else tr("gui.radius_file")),
            (tr("gui.material"), f"{material_text(m)}<br>a = {m['a']:.4f} Å, c = {m['c']:.4f} Å, "
                                 f"β a = {m['ab']:.4f} Å · {tr('mat.beta')}: "
                                 f"{(tr('mat.beta_auto'), tr('mat.beta_yes'), tr('mat.beta_no'))[('auto', 'yes', 'no').index(m['beta'])]}"
                                 f"<br>{tr('mat.refine')}: {yes(m['refine'])}"),
            (tr("wz.instrument"), (os.path.basename(c["inst_path"] or "") + "<br>" + "<br>".join(inst.describe()))
             if inst is not None else "–"),
            (tr("wz.zero_apply").split(" (")[0], yes(c["zero"])),
            (tr("wz.options"), f"{tr('gui.opt_wp')}: {yes(c['wp'])}<br>{tr('gui.ref_M')}: {c['M']:.2f}"
                               f"<br>{tr('gui.mc')}: {c['mc']}"),
        ]
        self.text.setHtml("<table cellspacing=6>" + "".join(
            f"<tr><td valign=top><b>{k}</b></td><td>{v}</td></tr>" for k, v in rows) + "</table>")


class AnalysisWizard(QWizard):
    """Optional assistant; ``cfg`` holds the settings, filled in page by page."""

    def __init__(self, parent, cfg, start_dir, offer=True):
        super().__init__(parent)
        self.cfg = dict(cfg)
        self.cfg["material"] = dict(cfg["material"])
        self.start_dir = start_dir
        self.saved_instrument = None
        self.setWindowTitle(tr("wz.title"))
        self.setWizardStyle(QWizard.ModernStyle)
        self.setOption(QWizard.NoBackButtonOnStartPage, True)
        self.setButtonText(QWizard.NextButton, tr("wz.next"))
        self.setButtonText(QWizard.BackButton, tr("wz.back"))
        self.setButtonText(QWizard.CancelButton, tr("wz.cancel"))
        self.setButtonText(QWizard.FinishButton, tr("gui.run"))
        self.resize(860, 760)
        self.intro = IntroPage(offer)
        self.pages = [self.intro, DataPage(), MaterialPage(), InstrumentPage(), OptionsPage(), SummaryPage()]
        for p in self.pages:
            self.addPage(p)

    @property
    def offer(self):
        return self.intro.offer.isChecked()
