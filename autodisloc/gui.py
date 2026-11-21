# SPDX-License-Identifier: MIT
# AutoDisloc 2 - Copyright (c) 2026 Firat Memu
"""AutoDisloc 2 desktop program (PySide6; identical on macOS and Windows).

Start:  python AutoDisloc2.py      (or the packaged app)
The interface language (Turkish / English) is switched in the toolbar.
"""

import os
import sys
import traceback

import numpy as np
from PySide6.QtCore import QObject, QSettings, Qt, QThread, QUrl, Signal
from PySide6.QtGui import QAction, QDesktopServices, QFont, QIcon
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QDoubleSpinBox, QFileDialog,
                               QFormLayout, QGroupBox, QHBoxLayout, QHeaderView, QLabel,
                               QListWidget, QListWidgetItem, QMainWindow, QMessageBox,
                               QPlainTextEdit, QProgressBar, QPushButton, QScrollArea, QSizePolicy,
                               QSpinBox, QSplitter, QTableWidget, QTableWidgetItem, QTabWidget,
                               QToolBar, QVBoxLayout, QWidget)
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg, NavigationToolbar2QT

from . import figures as F
from ._meta import AUTHOR, VERSION
from .export import export_package
from .i18n import default_language, get_language, set_language, tr
from .instrument import InstrumentModel, fit_instrument
from .io import ANODES, read_pattern
from .pipeline import AnalysisOptions, analyze
from .wizard import (KA2_CHOICES, RAD_KEYS, AnalysisWizard, MaterialDialog, RadiationDialog, StandardDialog,
                     material_cfg, material_text, show_file_info)
from . import materials

APP = "AutoDisloc 2"
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
BUNDLE = getattr(sys, "_MEIPASS", ROOT)
DEFAULT_INSTRUMENT = os.path.join(HERE, "data", "instrument_corundum_example.json")


def whitepaper_path():
    return os.path.join(BUNDLE, "docs", "whitepaper",
                        f"AutoDisloc2_Whitepaper_{get_language().upper()}.pdf")


def third_party_path():
    """Licence notices: bundled folder in the packaged program, the repository
    file when running from source."""
    p = os.path.join(BUNDLE, "third_party", "THIRD-PARTY-NOTICES.txt")
    return p if os.path.exists(p) else os.path.join(ROOT, "THIRD-PARTY-NOTICES.md")


def manual_path():
    return os.path.join(BUNDLE, "docs", "manual", f"AutoDisloc2_Manual_{get_language().upper()}.pdf")


STYLE = """
QMainWindow, QWidget { background: #fbfbfa; color: #1d1d1b; font-size: 13px; }
QGroupBox { border: 1px solid #e2e1dc; border-radius: 8px; margin-top: 14px; padding: 10px 8px 8px 8px;
            background: #ffffff; font-weight: 600; }
QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 4px; color: #52514e; }
QPushButton { background: #ffffff; border: 1px solid #d6d5cf; border-radius: 6px; padding: 6px 10px; }
QPushButton:hover { border-color: #2a78d6; }
QPushButton#primary { background: #2a78d6; color: white; border: none; font-weight: 600; padding: 9px; }
QPushButton#primary:hover { background: #256abf; }
QPushButton#primary:disabled { background: #9ec5f4; }
QPushButton#lang { padding: 4px 10px; font-weight: 600; border-radius: 0px; }
QPushButton#wizard { border-color: #2a78d6; color: #2a78d6; font-weight: 600; }
QScrollArea { border: none; }
QPushButton#lang:checked { background: #2a78d6; color: white; border-color: #2a78d6; }
QListWidget, QTableWidget, QPlainTextEdit { background: #ffffff; border: 1px solid #e2e1dc; border-radius: 6px; }
QTabWidget::pane { border: 1px solid #e2e1dc; border-radius: 8px; background: #ffffff; top: -1px; }
QTabBar::tab { padding: 7px 14px; margin-right: 2px; border-top-left-radius: 6px; border-top-right-radius: 6px;
               background: #f1f0ec; color: #52514e; }
QTabBar::tab:selected { background: #ffffff; color: #1d1d1b; font-weight: 600; }
QProgressBar { border: 1px solid #e2e1dc; border-radius: 5px; text-align: center; height: 16px; background: #ffffff; }
QProgressBar::chunk { background: #2a78d6; border-radius: 4px; }
QToolBar { background: #ffffff; border-bottom: 1px solid #e2e1dc; spacing: 6px; padding: 4px; }
QLabel#title { font-size: 18px; font-weight: 700; color: #1d1d1b; }
QLabel#muted { color: #6f6e69; }
QLabel#result { font-size: 15px; font-weight: 600; color: #1d1d1b; }
"""


# ---------------------------------------------------------------------------
class Worker(QObject):
    progress = Signal(int, str)
    done = Signal(list)
    failed = Signal(str)

    def __init__(self, items, inst, opts, read_kw):
        super().__init__()
        self.items, self.inst, self.opts, self.read_kw = items, inst, opts, read_kw

    def run(self):
        out = []
        try:
            for i, (p, name) in enumerate(self.items):
                self.progress.emit(i, tr("gui.progress", name=name))
                out.append(analyze(read_pattern(p, **self.read_kw), self.inst, name, self.opts))
            self.progress.emit(len(self.items), tr("gui.done"))
            self.done.emit(out)
        except Exception:
            self.failed.emit(traceback.format_exc())


class JournalCanvas(FigureCanvasQTAgg):
    """Keeps the journal proportions of the figure on screen: the dpi follows
    the widget size (the smaller of the width and height scales), so the
    whole figure stays visible and fonts look as they will in print."""

    def __init__(self, fig):
        self._w_in, self._h_in = fig.get_size_inches()
        super().__init__(fig)

    def resizeEvent(self, event):
        r = self.device_pixel_ratio
        w = max(event.size().width(), 50) * r
        h = max(event.size().height(), 50) * r
        self.figure.set_dpi(max(min(w / self._w_in, h / self._h_in), 40) / r)
        super().resizeEvent(event)


class FigurePanel(QWidget):
    """A matplotlib figure with the zoom/pan toolbar; replaced on update."""

    def __init__(self, hint):
        super().__init__()
        self.lay = QVBoxLayout(self)
        self.lay.setContentsMargins(6, 6, 6, 6)
        self.placeholder = QLabel(hint)
        self.placeholder.setAlignment(Qt.AlignCenter)
        self.placeholder.setObjectName("muted")
        self.lay.addWidget(self.placeholder)
        self.canvas = self.toolbar = self.figure = None

    def show_figure(self, fig):
        for w in (self.canvas, self.toolbar, self.placeholder):
            if w is not None:
                self.lay.removeWidget(w)
                w.setParent(None)
        self.placeholder = None
        self.figure = fig
        self.canvas = JournalCanvas(fig)
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.toolbar = NavigationToolbar2QT(self.canvas, self)
        self.lay.addWidget(self.toolbar)
        self.lay.addWidget(self.canvas)
        self.canvas.draw_idle()

    def show_message(self, text):
        """Replace the figure by a text (e.g. why it could not be drawn), so
        that no figure of a previous sample stays visible."""
        for w in (self.canvas, self.toolbar, self.placeholder):
            if w is not None:
                self.lay.removeWidget(w)
                w.setParent(None)
        self.canvas = self.toolbar = self.figure = None
        self.placeholder = QLabel(text)
        self.placeholder.setAlignment(Qt.AlignCenter)
        self.placeholder.setWordWrap(True)
        self.placeholder.setObjectName("muted")
        self.lay.addWidget(self.placeholder)


# (summary key, header i18n key or None for a symbol header, number format)
SUMMARY_COLS = [
    ("sample", "gui.h_sample", None),
    ("rho_text", "gui.h_rho", None),
    ("interval_method", "gui.h_method", None),
    ("M_star", "col.M_star", "{:.2f}"),
    ("h_a", None, "{:.2f}"),
    ("h_c", None, "{:.2f}"),
    ("h_ca", None, "{:.2f}"),
    ("b2c_hk0", None, "{:.4f}"),
    ("chi2_dof", None, "{:.2f}"),
    ("mwa_rho", "col.mwa_rho", "{:.2e}"),
    ("mwh_q1", None, "{:.2f}"),
    ("mwh_q2", None, "{:.2f}"),
    ("mwh_D_nm", None, "{:.0f}"),
    ("a_A", None, "{:.4f}"),
    ("c_A", None, "{:.4f}"),
    ("ca", None, "{:.4f}"),
    ("a_beta_A", None, "{:.4f}"),
]
SYMBOL_HEAD = {"h_a": "h ⟨a⟩", "h_c": "h ⟨c⟩", "h_ca": "h ⟨c+a⟩", "b2c_hk0": "b²C̄ (nm²)",
               "chi2_dof": "χ²/dof", "mwh_q1": "q₁", "mwh_q2": "q₂", "mwh_D_nm": "D (nm)",
               "a_A": "α a (Å)", "c_A": "α c (Å)", "ca": "α c/a", "a_beta_A": "β a (Å)"}


class MainWindow(QMainWindow):
    def __init__(self, state=None):
        super().__init__()
        self.setWindowTitle(f"{APP} — {tr('gui.subtitle')}")
        self.resize(1440, 900)
        self.settings = QSettings("FiratMemu", "AutoDisloc2")
        self.inst = None
        self.inst_path = None
        self.results = []
        self.thread = None
        self.custom_rad = (1.540598, 1.544426, 0.5)
        self.material = material_cfg("Ti-6Al-4V")
        self.zero_apply = False
        self._fig_errors = []          # figures that could not be drawn (shown in Warnings)
        self._build()
        if state:
            self._restore(state)
        else:
            last = self.settings.value("instrument", "")
            path = last if last and os.path.exists(last) else DEFAULT_INSTRUMENT
            if os.path.exists(path):
                self._set_instrument(InstrumentModel.load(path), path)

    # ---------------- layout ----------------
    def _build(self):
        tb = QToolBar()
        tb.setMovable(False)
        self.addToolBar(tb)
        tb.addWidget(QLabel(tr("gui.sample")))
        self.sample_box = QComboBox()
        self.sample_box.setMinimumWidth(160)
        self.sample_box.currentIndexChanged.connect(self._show_sample)
        tb.addWidget(self.sample_box)
        tb.addSeparator()
        for key, fn in (("gui.save_fig", self._export_current), ("gui.export_all", self._export_all)):
            a = QAction(tr(key), self)
            a.triggered.connect(fn)
            tb.addAction(a)
        tb.addSeparator()
        for key, fn in (("gui.manual", self._open_manual), ("gui.whitepaper", self._open_whitepaper),
                        ("gui.about", self._about)):
            a = QAction(tr(key), self)
            a.triggered.connect(fn)
            tb.addAction(a)
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        tb.addWidget(spacer)
        box = QWidget()
        bl = QHBoxLayout(box)
        bl.setContentsMargins(0, 0, 6, 0)
        bl.setSpacing(0)
        self.lang_buttons = {}
        for lang in ("tr", "en"):
            b = QPushButton(lang.upper())
            b.setObjectName("lang")
            b.setCheckable(True)
            b.setChecked(lang == get_language())
            b.setToolTip(tr("gui.lang_tip"))
            b.clicked.connect(lambda _=False, l=lang: self._switch_language(l))
            bl.addWidget(b)
            self.lang_buttons[lang] = b
        tb.addWidget(box)

        split = QSplitter()
        self.setCentralWidget(split)
        split.addWidget(self._sidebar())
        self.tabs = QTabWidget()
        split.addWidget(self.tabs)
        split.setSizes([330, 1110])

        self.panels = {}
        ov = QWidget()
        ol = QVBoxLayout(ov)
        self.headline = QLabel(tr("gui.start_hint"))
        self.headline.setObjectName("result")
        self.headline.setWordWrap(True)
        ol.addWidget(self.headline)
        self.panels["compare"] = FigurePanel(tr("gui.compare_hint"))
        ol.addWidget(self.panels["compare"], 3)
        self.table = QTableWidget()
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        ol.addWidget(self.table, 2)
        self.tabs.addTab(ov, tr("gui.tab_summary"))
        for key in ("pattern", "wp", "mwh", "mwa", "burgers", "fourier", "lattice", "instrument"):
            self.panels[key] = FigurePanel(tr("gui.hint_" + key))
            self.tabs.addTab(self.panels[key], tr("gui.tab_" + key))
        self.warn_box = QPlainTextEdit()
        self.warn_box.setReadOnly(True)
        self.tabs.addTab(self.warn_box, tr("gui.tab_warnings"))
        self.peaks_table = QTableWidget()
        self.tabs.addTab(self.peaks_table, tr("gui.tab_peaks"))

    def _sidebar(self):
        """Settings in a scroll area; the run button, progress and status stay
        visible below it."""
        side = QWidget()
        side.setMinimumWidth(340)
        side.setMaximumWidth(420)
        outer = QVBoxLayout(side)
        outer.setContentsMargins(0, 0, 0, 0)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        w = QWidget()
        scroll.setWidget(w)
        outer.addWidget(scroll, 1)
        lay = QVBoxLayout(w)
        t = QLabel(APP)
        t.setObjectName("title")
        t.setToolTip(f"© {AUTHOR}")
        lay.addWidget(t)
        s = QLabel(tr("gui.version", v=VERSION))
        s.setObjectName("muted")
        s.setWordWrap(True)
        lay.addWidget(s)
        b = QPushButton(tr("gui.wizard"))
        b.setObjectName("wizard")
        b.setToolTip(tr("gui.wizard_tip"))
        b.clicked.connect(lambda: self._open_wizard())
        lay.addWidget(b)

        g = QGroupBox(tr("gui.g_instrument"))
        gl = QVBoxLayout(g)
        self.inst_label = QLabel(tr("gui.not_loaded"))
        self.inst_label.setWordWrap(True)
        self.inst_label.setObjectName("muted")
        gl.addWidget(self.inst_label)
        for key, fn in (("gui.load_inst", self._load_instrument), ("gui.build_inst", self._build_instrument)):
            b = QPushButton(tr(key))
            b.clicked.connect(fn)
            gl.addWidget(b)
        lay.addWidget(g)

        g = QGroupBox(tr("gui.g_samples"))
        gl = QVBoxLayout(g)
        self.file_list = QListWidget()
        self.file_list.setMinimumHeight(110)
        self.file_list.setMaximumHeight(170)
        gl.addWidget(self.file_list)
        row = QHBoxLayout()
        b = QPushButton(tr("gui.add"))
        b.clicked.connect(self._add_files)
        row.addWidget(b)
        b = QPushButton(tr("gui.remove"))
        b.clicked.connect(lambda: [self.file_list.takeItem(self.file_list.row(i))
                                   for i in self.file_list.selectedItems()])
        row.addWidget(b)
        gl.addLayout(row)
        b = QPushButton(tr("gui.file_info"))
        b.clicked.connect(self._file_info)
        gl.addWidget(b)
        lay.addWidget(g)

        g = QGroupBox(tr("gui.g_measure"))
        fl = QFormLayout(g)
        self.opt_rad = QComboBox()
        self.opt_rad.addItems([tr("gui.rad_file")] + [tr("wz.rad_preset", a=k) for k in ANODES]
                              + [tr("gui.rad_custom")])
        self.opt_rad.setToolTip(tr("gui.rad_tip"))
        self._rad_index = 0
        self.opt_rad.activated.connect(self._radiation_chosen)
        fl.addRow(tr("gui.radiation"), self.opt_rad)
        self.opt_ka2 = QComboBox()
        self.opt_ka2.addItems([tr("gui.ka2_auto"), tr("gui.ka2_present"), tr("gui.ka2_stripped")])
        self.opt_ka2.setToolTip(tr("gui.ka2_tip"))
        fl.addRow(tr("gui.ka2"), self.opt_ka2)
        self.opt_radius = QDoubleSpinBox()
        self.opt_radius.setRange(0, 1000)
        self.opt_radius.setDecimals(1)
        self.opt_radius.setSuffix(" mm")
        self.opt_radius.setSpecialValueText(tr("gui.radius_file"))
        self.opt_radius.setToolTip(tr("gui.radius_tip"))
        fl.addRow(tr("gui.radius"), self.opt_radius)
        self.opt_mat = QComboBox()
        self.opt_mat.addItems([materials.display_name(k) for k in materials.MATERIAL_KEYS[:-1]]
                              + [tr("gui.mat_custom")])
        self.opt_mat.setToolTip(tr("mat.note"))
        self.opt_mat.activated.connect(self._material_chosen)
        fl.addRow(tr("gui.material"), self.opt_mat)
        lay.addWidget(g)

        g = QGroupBox(tr("gui.g_options"))
        fl = QFormLayout(g)
        self.opt_wp = QCheckBox(tr("gui.opt_wp"))
        self.opt_wp.setChecked(True)
        fl.addRow(self.opt_wp)
        self.opt_mwh = QComboBox()
        self.opt_mwh.addItems([tr("gui.mwh_con"), tr("gui.mwh_free")])
        fl.addRow("mWH", self.opt_mwh)
        self.opt_fourier = QComboBox()
        self.opt_fourier.addItems([tr("gui.four_voigt"), tr("gui.four_eq13")])
        # the second entry is long: do not let it widen the side panel
        self.opt_fourier.setSizeAdjustPolicy(QComboBox.AdjustToMinimumContentsLengthWithIcon)
        self.opt_fourier.setMinimumContentsLength(18)
        fl.addRow("Voigt-mWA", self.opt_fourier)
        self.opt_M = QDoubleSpinBox()
        self.opt_M.setRange(0.3, 10)
        self.opt_M.setSingleStep(0.05)
        self.opt_M.setValue(2.64)
        self.opt_M.setToolTip(tr("gui.ref_M_tip"))
        lab_M = QLabel(tr("gui.ref_M"))
        lab_M.setToolTip(tr("gui.ref_M_tip"))
        fl.addRow(lab_M, self.opt_M)
        self.opt_mc = QSpinBox()
        self.opt_mc.setRange(0, 1000)
        self.opt_mc.setValue(100)
        fl.addRow(tr("gui.mc"), self.opt_mc)
        lay.addWidget(g)
        note = QLabel(tr("gui.note"))
        note.setWordWrap(True)
        note.setObjectName("muted")
        lay.addWidget(note)
        lay.addStretch(1)

        bottom = QWidget()
        bl = QVBoxLayout(bottom)
        bl.setContentsMargins(9, 4, 9, 9)
        self.run_btn = QPushButton(tr("gui.run"))
        self.run_btn.setObjectName("primary")
        self.run_btn.clicked.connect(lambda: self._run())
        bl.addWidget(self.run_btn)
        self.progress = QProgressBar()
        self.progress.setValue(0)
        bl.addWidget(self.progress)
        self.status = QLabel("")
        self.status.setWordWrap(True)
        self.status.setObjectName("muted")
        bl.addWidget(self.status)
        outer.addWidget(bottom)
        return side

    # ---------------- language ----------------
    def _state(self):
        return {"inst": self.inst, "inst_path": self.inst_path, "results": self.results,
                "files": [(self.file_list.item(i).data(Qt.UserRole), self.file_list.item(i).text())
                          for i in range(self.file_list.count())],
                "opts": (self.opt_wp.isChecked(), self.opt_ka2.currentIndex(), self.opt_mwh.currentIndex(),
                         self.opt_fourier.currentIndex(), self.opt_M.value(), self.opt_mc.value()),
                "cfg": self._cfg(),
                "tab": self.tabs.currentIndex(), "sample": self.sample_box.currentIndex(),
                "geometry": self.saveGeometry()}

    def _restore(self, st):
        if st["inst"] is not None:
            self._set_instrument(st["inst"], st["inst_path"])
        for p, name in st["files"]:
            self._add_item(p, name)
        wp, ka2, mwh, four, M, mc = st["opts"]
        self.opt_wp.setChecked(wp)
        self.opt_ka2.setCurrentIndex(ka2)
        self.opt_mwh.setCurrentIndex(mwh)
        self.opt_fourier.setCurrentIndex(four)
        self.opt_M.setValue(M)
        self.opt_mc.setValue(mc)
        c = st.get("cfg")
        if c:
            self.custom_rad = c["radiation"] if isinstance(c["radiation"], tuple) else self.custom_rad
            self._set_radiation(c["radiation"])
            self.opt_radius.setValue(c["radius"] or 0)
            self._set_material(c["material"])
            self.zero_apply = c["zero"]
        self.restoreGeometry(st["geometry"])
        if st["results"]:
            self._finished(st["results"])
            self.sample_box.setCurrentIndex(max(st["sample"], 0))
        self.tabs.setCurrentIndex(st["tab"])

    def _switch_language(self, lang):
        busy = self.thread is not None and self.thread.isRunning()
        if lang == get_language() or busy:
            for l, b in self.lang_buttons.items():
                b.setChecked(l == get_language())
            return
        set_language(lang)
        self.settings.setValue("lang", lang)
        new = MainWindow(self._state())
        QApplication.instance()._main_window = new
        new.show()
        self.close()

    # ---------------- misc ----------------
    def _about(self):
        box = QMessageBox(self)
        box.setWindowTitle(APP)
        box.setTextFormat(Qt.RichText)
        box.setText(tr("gui.about_text", v=VERSION))
        lic = box.addButton(tr("gui.third_party"), QMessageBox.ActionRole)
        box.addButton(QMessageBox.Ok)
        box.exec()
        if box.clickedButton() is lic:
            p = third_party_path()
            if os.path.exists(p):
                QDesktopServices.openUrl(QUrl.fromLocalFile(p))
            else:
                QMessageBox.information(self, APP, tr("gui.no_whitepaper", p=p))

    def _open_manual(self):
        p = manual_path()
        if not os.path.exists(p):
            QMessageBox.information(self, APP, tr("gui.no_whitepaper", p=p))
            return
        QDesktopServices.openUrl(QUrl.fromLocalFile(p))

    def _open_whitepaper(self):
        p = whitepaper_path()
        if not os.path.exists(p):
            QMessageBox.information(self, APP, tr("gui.no_whitepaper", p=p))
            return
        QDesktopServices.openUrl(QUrl.fromLocalFile(p))

    # ---------------- instrument ----------------
    def _set_instrument(self, inst, path):
        self.inst, self.inst_path = inst, path
        name = os.path.basename(path)
        if os.path.abspath(path) == os.path.abspath(DEFAULT_INSTRUMENT):
            name += tr("gui.inst_example")
        txt = tr("gui.inst_label", name=name, k0=inst.k_range[0], k1=inst.k_range[1])
        extra = inst.describe()
        self.inst_label.setText(txt + ("\n" + " · ".join(extra) if extra else ""))
        self.panels["instrument"].show_figure(F.fig_instrument(inst))

    def _load_instrument(self):
        p, _ = QFileDialog.getOpenFileName(self, tr("gui.dlg_inst"), self._last_dir(), "JSON (*.json)")
        if p:
            self._set_instrument(InstrumentModel.load(p), p)
            self.settings.setValue("instrument", p)

    def _build_instrument(self):
        dlg = StandardDialog(self, self._last_dir(), self.settings.value("standard", "corundum"))
        if not dlg.exec():
            return
        p = dlg.path
        c = self._cfg()
        self.settings.setValue("standard", dlg.form.key())
        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            inst = fit_instrument(p, degree=dlg.form.degree.value(), ka2_stripped=c["ka2"],
                                  standard=dlg.form.key(), lattice=dlg.form.lattice(),
                                  radiation=c["radiation"], radius_mm=c["radius"], name=os.path.basename(p))
        except Exception as e:
            QApplication.restoreOverrideCursor()
            QMessageBox.warning(self, APP, tr("gui.std_failed", e=e))
            return
        QApplication.restoreOverrideCursor()
        if getattr(inst, "fit_warnings", None):
            QMessageBox.information(self, APP, "\n\n".join(str(w) for w in inst.fit_warnings))
        out, _ = QFileDialog.getSaveFileName(self, tr("gui.dlg_save_inst"),
                                             os.path.splitext(p)[0] + tr("gui.inst_suffix"), "JSON (*.json)")
        if out:
            inst.save(out)
            self.settings.setValue("instrument", out)
        self._set_instrument(inst, out or p)
        self.tabs.setCurrentWidget(self.panels["instrument"])

    # ---------------- samples ----------------
    def _last_dir(self):
        return self.settings.value("last_dir", os.path.expanduser("~"))

    def _add_item(self, p, name):
        it = QListWidgetItem(name)
        it.setData(Qt.UserRole, p)
        it.setToolTip(tr("gui.item_tip", p=p))
        it.setFlags(it.flags() | Qt.ItemIsEditable)
        self.file_list.addItem(it)

    def _add_files(self):
        ps, _ = QFileDialog.getOpenFileNames(self, tr("gui.dlg_samples"), self._last_dir(), tr("gui.file_filter"))
        for p in ps:
            self._add_item(p, os.path.splitext(os.path.basename(p))[0])
        if ps:
            self.settings.setValue("last_dir", os.path.dirname(ps[0]))
            self._check_metadata(ps)

    def _check_metadata(self, paths):
        """Status note when files contain no wavelength and no radiation is chosen."""
        if RAD_KEYS[self.opt_rad.currentIndex()] is not None:
            return
        n, unreadable = 0, []
        for p in paths:
            try:
                n += "wavelength" in read_pattern(p).assumed
            except Exception as e:
                unreadable.append(f"{os.path.basename(p)}: {e}")
        notes = [tr("gui.assumed_note", n=n)] if n else []
        notes += [tr("gui.unreadable", f=u) for u in unreadable]
        if notes:
            self.status.setText("\n".join(notes))

    def _file_info(self):
        it = self.file_list.currentItem() or (self.file_list.item(0) if self.file_list.count() else None)
        if it is None:
            QMessageBox.information(self, APP, tr("gui.need_samples"))
            return
        c = self._cfg()
        show_file_info(self, it.data(Qt.UserRole), c["radiation"], c["radius"], c["ka2"])

    # ---------------- measurement & material ----------------
    def _radiation_chosen(self, i):
        if RAD_KEYS[i] == "custom":
            dlg = RadiationDialog(self, self.custom_rad)
            if not dlg.exec():
                self.opt_rad.setCurrentIndex(self._rad_index)
                return
            self.custom_rad = dlg.value()
            self.opt_rad.setItemText(i, tr("gui.rad_custom_set", wl1=self.custom_rad[0]))
        self._rad_index = i

    def _set_radiation(self, rad):
        if rad is None or isinstance(rad, str):
            self.opt_rad.setCurrentIndex(RAD_KEYS.index(rad))
        else:
            self.custom_rad = tuple(rad)
            i = len(RAD_KEYS) - 1
            self.opt_rad.setItemText(i, tr("gui.rad_custom_set", wl1=rad[0]))
            self.opt_rad.setCurrentIndex(i)
        self._rad_index = self.opt_rad.currentIndex()

    def _material_chosen(self, i):
        key = materials.MATERIAL_KEYS[i]
        if key == "custom":
            m = dict(self.material)
            m["key"] = "custom"
            dlg = MaterialDialog(self, m)
            if not dlg.exec():
                self._set_material(self.material)
                return
            self._set_material(dlg.value())
        else:
            self._set_material(material_cfg(key, self.material.get("refine", True)))

    def _set_material(self, m):
        self.material = dict(m)
        i = materials.MATERIAL_KEYS.index(m["key"])
        last = len(materials.MATERIAL_KEYS) - 1
        self.opt_mat.setItemText(last, material_text(m) if m["key"] == "custom" else tr("gui.mat_custom"))
        self.opt_mat.setCurrentIndex(i)
        self.opt_mat.setToolTip(f"a = {m['a']:.4f} Å, c = {m['c']:.4f} Å, β a = {m['ab']:.4f} Å\n" + tr("mat.note"))

    def _cfg(self):
        """All analysis settings as one dict (shared with the assistant)."""
        key = RAD_KEYS[self.opt_rad.currentIndex()]
        return {
            "files": [(self.file_list.item(i).data(Qt.UserRole), self.file_list.item(i).text())
                      for i in range(self.file_list.count())],
            "radiation": tuple(self.custom_rad) if key == "custom" else key,
            "radius": self.opt_radius.value() or None,
            "ka2": KA2_CHOICES[self.opt_ka2.currentIndex()],
            "material": dict(self.material),
            "inst": self.inst, "inst_path": self.inst_path, "zero": self.zero_apply,
            "wp": self.opt_wp.isChecked(), "mwh": self.opt_mwh.currentIndex(),
            "fourier": self.opt_fourier.currentIndex(), "M": self.opt_M.value(), "mc": self.opt_mc.value(),
        }

    def _apply_cfg(self, c):
        self.file_list.clear()
        for p, name in c["files"]:
            self._add_item(p, name)
        self._set_radiation(c["radiation"])
        self.opt_radius.setValue(c["radius"] or 0)
        self.opt_ka2.setCurrentIndex(KA2_CHOICES.index(c["ka2"]))
        self._set_material(c["material"])
        if c["inst"] is not None and c["inst"] is not self.inst:
            self._set_instrument(c["inst"], c["inst_path"] or "")
            if c["inst_path"] and c["inst_path"].lower().endswith(".json"):
                self.settings.setValue("instrument", c["inst_path"])
        self.zero_apply = c["zero"]
        self.opt_wp.setChecked(c["wp"])
        self.opt_mwh.setCurrentIndex(c["mwh"])
        self.opt_fourier.setCurrentIndex(c["fourier"])
        self.opt_M.setValue(c["M"])
        self.opt_mc.setValue(c["mc"])

    def _open_wizard(self, run=True):
        offer = self.settings.value("offer_wizard", True, type=bool)
        wz = AnalysisWizard(self, self._cfg(), self._last_dir(), offer)
        ok = wz.exec()
        self.settings.setValue("offer_wizard", wz.offer)
        self.settings.setValue("last_dir", wz.start_dir)
        if wz.saved_instrument:
            self.settings.setValue("instrument", wz.saved_instrument)
        if not ok:
            return False
        self._apply_cfg(wz.cfg)
        if run:
            self._run(offer=False)
        return True

    def _options(self):
        m = self.material
        return AnalysisOptions(
            whole_profile=self.opt_wp.isChecked(),
            mwh_mode="constrained" if self.opt_mwh.currentIndex() == 0 else "free",
            fourier_mode="voigt" if self.opt_fourier.currentIndex() == 0 else "eq13",
            wp_M_ref=self.opt_M.value(), mc_draws=self.opt_mc.value(),
            material=m["key"], nominal_lattice=(m["a"], m["c"], m["ab"]), beta=m["beta"],
            refine_nominal=m.get("refine", True), apply_zero_shift=self.zero_apply)

    def _offer_wizard(self):
        """Optional: ask once per run whether to use the assistant. Returns True
        when the assistant took over."""
        if not self.settings.value("offer_wizard", True, type=bool):
            return False
        box = QMessageBox(self)
        box.setWindowTitle(tr("gui.offer_title"))
        box.setText(tr("gui.offer_text"))
        wiz = box.addButton(tr("gui.offer_wizard"), QMessageBox.AcceptRole)
        direct = box.addButton(tr("gui.offer_direct"), QMessageBox.RejectRole)
        box.setDefaultButton(direct)
        never = QCheckBox(tr("gui.offer_never"))
        box.setCheckBox(never)
        box.exec()
        if never.isChecked():
            self.settings.setValue("offer_wizard", False)
        if box.clickedButton() is wiz:
            self._open_wizard()
            return True
        return False

    def _run(self, offer=True):
        if offer and self._offer_wizard():
            return
        items = [(self.file_list.item(i).data(Qt.UserRole),
                  self.file_list.item(i).text().strip() or tr("sample_default", n=i + 1))
                 for i in range(self.file_list.count())]
        if not items:
            QMessageBox.information(self, APP, tr("gui.need_samples"))
            return
        if self.inst is None:
            QMessageBox.information(self, APP, tr("gui.need_inst"))
            return
        self.run_btn.setEnabled(False)
        self.progress.setRange(0, len(items))
        self.progress.setValue(0)
        self.thread = QThread()
        c = self._cfg()
        self.worker = Worker(items, self.inst, self._options(),
                             {"ka2_stripped": c["ka2"], "radiation": c["radiation"], "radius_mm": c["radius"]})
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.progress.connect(lambda i, m: (self.progress.setValue(i), self.status.setText(m)))
        self.worker.done.connect(self._finished)
        self.worker.failed.connect(self._failed)
        self.worker.done.connect(self.thread.quit)
        self.worker.failed.connect(self.thread.quit)
        self.thread.start()

    def _failed(self, msg):
        self.run_btn.setEnabled(True)
        self.status.setText(tr("gui.error"))
        QMessageBox.critical(self, APP, msg[-3000:])

    def _finished(self, results):
        self.run_btn.setEnabled(True)
        self.results = results
        self.sample_box.blockSignals(True)
        self.sample_box.clear()
        self.sample_box.addItems([r.sample for r in results])
        self.sample_box.blockSignals(False)
        self._fill_summary()
        self.panels["compare"].show_figure(F.fig_compare(results))
        self._fig_errors = []
        self._draw("lattice", F.fig_lattice, results, self._fig_errors)
        self._show_sample(0)
        self.tabs.setCurrentIndex(0)

    # ---------------- display ----------------
    def _fill_summary(self):
        rows = [r.summary() for r in self.results]
        self.table.setColumnCount(len(SUMMARY_COLS))
        self.table.setRowCount(len(rows))
        self.table.setHorizontalHeaderLabels([tr(h) if h else SYMBOL_HEAD[k] for k, h, _ in SUMMARY_COLS])
        for i, d in enumerate(rows):
            for j, (key, _, fmt) in enumerate(SUMMARY_COLS):
                v = d.get(key, "")
                if fmt and isinstance(v, (float, np.floating)):
                    v = "–" if not np.isfinite(v) else fmt.format(v)
                it = QTableWidgetItem(str(v))
                if j == 1:
                    f = QFont()
                    f.setBold(True)
                    it.setFont(f)
                self.table.setItem(i, j, it)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.headline.setText("  ·  ".join(tr("gui.headline", s=d["sample"], v=d["rho_text"].split(" (")[0])
                                             for d in rows))

    def _show_sample(self, idx):
        if not self.results or idx < 0:
            return
        r = self.results[idx]
        errors = list(self._fig_errors)
        for key, fn in [("pattern", F.fig_pattern), ("mwh", F.fig_mwh), ("mwa", F.fig_mwa),
                        ("burgers", F.fig_burgers)]:
            self._draw(key, fn, r, errors)
        if r.wp is not None:
            self._draw("wp", F.fig_wholeprofile, r, errors)
            self._draw("fourier", F.fig_fourier_components, r, errors)
        else:
            # no whole-profile result for this sample: do not leave another sample's figure
            for key in ("wp", "fourier"):
                self.panels[key].show_message(tr("gui.no_wp"))
        lines = [str(w) for w in r.warnings] + errors
        self.warn_box.setPlainText("\n".join("• " + w for w in lines) or tr("no_warnings"))
        if errors:
            self.status.setText(errors[-1])
        t = r.peaks
        self.peaks_table.setColumnCount(len(t.columns))
        self.peaks_table.setRowCount(len(t))
        self.peaks_table.setHorizontalHeaderLabels([str(c) for c in t.columns])
        for i in range(len(t)):
            for j, c in enumerate(t.columns):
                v = t.iloc[i, j]
                s = f"{v:.5g}" if isinstance(v, (float, np.floating)) else str(v)
                self.peaks_table.setItem(i, j, QTableWidgetItem(s))

    def _draw(self, key, fn, arg, errors):
        """Draw one figure tab; a failure is shown in the tab, in the Warnings
        tab and in the status line instead of leaving the tab silently empty."""
        try:
            self.panels[key].show_figure(fn(arg))
        except Exception as e:
            msg = tr("gui.fig_failed", tab=tr("gui.tab_" + key), err=f"{type(e).__name__}: {e}")
            self.panels[key].show_message(msg)
            errors.append(msg)

    # ---------------- export ----------------
    def _export_current(self):
        w = self.tabs.currentWidget()
        if w is self.tabs.widget(0):
            w = self.panels["compare"]
        if not isinstance(w, FigurePanel) or w.figure is None:
            QMessageBox.information(self, APP, tr("gui.no_fig"))
            return
        p, _ = QFileDialog.getSaveFileName(self, tr("gui.dlg_save_fig"),
                                           os.path.join(self._last_dir(), tr("gui.fig_name")),
                                           tr("gui.fig_filter"))
        if p:
            F.save_figure(w.figure, p)
            self.status.setText(tr("gui.saved", p=p))

    def _export_all(self):
        if not self.results:
            QMessageBox.information(self, APP, tr("gui.need_run"))
            return
        d = QFileDialog.getExistingDirectory(self, tr("gui.dlg_package"), self._last_dir())
        if not d:
            return
        export_package(self.results, d, self.inst)
        self.status.setText(tr("gui.package_done", d=d))
        QDesktopServices.openUrl(QUrl.fromLocalFile(d))


def selftest(paths, out, lang=None):
    """Headless check of a (packaged) build: analyse and export."""
    if lang:
        set_language(lang)
    inst = InstrumentModel.load(DEFAULT_INSTRUMENT)
    res = [analyze(read_pattern(p), inst, os.path.splitext(os.path.basename(p))[0],
                   AnalysisOptions(mc_draws=20)) for p in paths]
    export_package(res, out, inst)
    for r in res:
        s = r.summary()
        print(r.sample, s["rho_text"], str(s["interval_method"]))
    return 0


def main():
    if len(sys.argv) > 2 and sys.argv[1] == "--selftest":
        args = sys.argv[2:]
        lang = None
        if args[0] in ("--lang=tr", "--lang=en"):
            lang, args = args[0][-2:], args[1:]
        return selftest(args[:-1], args[-1], lang)
    app = QApplication(sys.argv)
    app.setApplicationName(APP)
    app.setOrganizationName("Firat Memu")
    app.setStyleSheet(STYLE)
    lang = QSettings("FiratMemu", "AutoDisloc2").value("lang", "")
    set_language(lang if lang in ("tr", "en") else default_language())
    icon = os.path.join(BUNDLE, "assets", "icon.png")
    if os.path.exists(icon):
        app.setWindowIcon(QIcon(icon))
    app._main_window = MainWindow()
    app._main_window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
