# SPDX-License-Identifier: MIT
# AutoDisloc 2 - Copyright (c) 2026 Firat Memu
"""Screenshots of the desktop program for the user manual (both languages).

    QT_QPA_PLATFORM=offscreen python docs/manual/make_screenshots.py

Uses the analysed synthetic examples (whitepaper cache) so that every tab
shows real results. Numbered callouts are drawn on the main window."""

import os
import pickle
import sys
import warnings

warnings.filterwarnings("ignore")
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, ROOT)

from PIL import Image, ImageDraw, ImageFont  # noqa: E402
from PySide6.QtCore import QPoint  # noqa: E402
from PySide6.QtWidgets import QApplication, QGroupBox  # noqa: E402

from autodisloc import gui, set_language  # noqa: E402

EXAMPLES = [("A", os.path.join(ROOT, "examples", "synthetic_Ti64_A.xy")),
            ("B", os.path.join(ROOT, "examples", "synthetic_Ti64_B.xy"))]
W, H = 1480, 1180
ORANGE = (235, 104, 52)


def rect(win, w):
    p = w.mapTo(win, QPoint(0, 0))
    return p.x(), p.y(), w.width(), w.height()


TOP = 40  # band above the window for the toolbar callouts


def callouts(path, marks):
    """marks: (number, (x, y), on_top). On-top marks are drawn in a band above
    the screenshot with a leader line to the widget."""
    src = Image.open(path).convert("RGB")
    im = Image.new("RGB", (src.width, src.height + TOP), "white")
    im.paste(src, (0, TOP))
    d = ImageDraw.Draw(im)
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 16)
    except OSError:
        font = ImageFont.load_default()
    r = 13
    for n, (x, y), top in marks:
        if top:
            d.line([(x, TOP / 2 + r), (x, TOP + y)], fill=ORANGE, width=2)
            cx, cy = x, TOP / 2
        else:
            cx, cy = x, y + TOP
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=ORANGE, outline="white", width=2)
        t = str(n)
        d.text((cx - d.textlength(t, font=font) / 2, cy - 9), t, fill="white", font=font)
    im.save(path)


def wizard_shots(app, out):
    """Assistant pages 1 (data) and 3 (instrument). Page 1 shows the two
    examples (complete header) and a copy without header (assumed values);
    page 3 builds a model from a standard pattern when one is given in
    AUTODISLOC_STANDARD_PATTERN (path of a corundum pattern file), else it
    shows the current model."""
    import shutil
    import tempfile
    tmp = tempfile.mkdtemp()
    plain = os.path.join(tmp, "my_measurement.xy")
    with open(EXAMPLES[0][1]) as f, open(plain, "w") as g:
        g.writelines(l for l in f if not l.startswith("#"))
    w = gui.MainWindow()
    for name, p in EXAMPLES:
        w._add_item(p, "synthetic_Ti64_" + name)
    w._add_item(plain, "my_measurement")
    wz = gui.AnalysisWizard(w, w._cfg(), tmp, True)
    wz.show()
    app.processEvents()
    wz.next()
    app.processEvents()
    wz.grab().save(os.path.join(out, "wz_data.png"))
    wz.next()
    app.processEvents()
    wz.next()
    app.processEvents()
    page = wz.currentPage()
    std = os.environ.get("AUTODISLOC_STANDARD_PATTERN", "")
    if std and os.path.exists(std):
        page.r_build.setChecked(True)
        page.std_path = std
        page.std_lab.setText(os.path.basename(std))
        page._fit()
        app.processEvents()
    wz.grab().save(os.path.join(out, "wz_instrument.png"))
    wz.close()
    w.close()
    shutil.rmtree(tmp, ignore_errors=True)


def main():
    app = QApplication.instance() or QApplication(sys.argv)
    app.setStyleSheet(gui.STYLE)
    cache = os.path.join(HERE, "_screens_results.pkl")
    if os.path.exists(cache):
        results = pickle.load(open(cache, "rb"))
    else:
        from autodisloc import InstrumentModel, analyze, read_pattern
        inst = InstrumentModel.load(gui.DEFAULT_INSTRUMENT)
        results = [analyze(read_pattern(p), inst, n) for n, p in EXAMPLES]
        pickle.dump(results, open(cache, "wb"))
    for lang in ("tr", "en"):
        set_language(lang)
        out = os.path.join(HERE, f"img_{lang}")
        os.makedirs(out, exist_ok=True)

        # start screen (before an analysis)
        w0 = gui.MainWindow()
        w0.resize(W, H)
        w0.show()
        app.processEvents()
        w0.grab().save(os.path.join(out, "00_start.png"))
        w0.close()

        win = gui.MainWindow()
        win.resize(W, H)
        for name, p in EXAMPLES:
            win._add_item(p, name)
        win.show()
        app.processEvents()
        win._finished(results)
        app.processEvents()
        main_png = os.path.join(out, "01_main.png")
        win.grab().save(main_png)

        # callout positions
        tb = win.findChildren(gui.QToolBar)[0]
        acts = {a.text(): tb.widgetForAction(a) for a in tb.actions() if tb.widgetForAction(a)}
        from autodisloc.i18n import tr
        groups = win.findChildren(QGroupBox)
        wiz_btn = [b for b in win.findChildren(gui.QPushButton) if b.objectName() == "wizard"][0]

        def tl(w, dx=10, dy=10):
            x, y, _, _ = rect(win, w)
            return x + dx, y + dy

        def at(w, fx, dy, top=False, dx=0):
            x, y, ww, hh = rect(win, w)
            return (x + fx * ww + dx, y + dy), top

        spec = [
            (1, win.lang_buttons["tr"], 1.0, 4, True, 0),
            (2, win.sample_box, 0.5, 4, True, 0),
            (3, acts[tr("gui.save_fig")], 0.5, 4, True, 0),
            (4, acts[tr("gui.export_all")], 0.5, 4, True, 0),
            (5, acts[tr("gui.manual")], 0.5, 4, True, 0),
            (6, wiz_btn, 1.0, 14, False, -18),
            (7, groups[0], 1.0, 12, False, -24),
            (8, groups[1], 1.0, 12, False, -24),
            (9, groups[2], 1.0, 12, False, -24),
            (10, groups[3], 1.0, 12, False, -24),
            (11, win.run_btn, 1.0, 17, False, -24),
            (12, win.tabs.tabBar(), 1.0, 14, False, 20),
            (13, win.headline, 0.55, 10, False, 0),
            (14, win.panels["compare"], 1.0, 60, False, -40),
            (15, win.table, 0.0, 130, False, 40),
        ]
        marks = [(n,) + at(w, fx, dy, top, dx) for n, w, fx, dy, top, dx in spec]
        callouts(main_png, marks)

        # sidebar crop (whole left panel incl. run button)
        x, y, w, h = rect(win, win.run_btn.parentWidget().parentWidget())
        Image.open(os.path.join(out, "00_start.png")).crop((x, y, x + w, y + h)).save(os.path.join(out, "02_sidebar.png"))

        keys = ["summary", "pattern", "wp", "mwh", "mwa", "burgers", "fourier", "lattice", "instrument", "warnings", "peaks"]
        for i, k in enumerate(keys):
            win.tabs.setCurrentIndex(i)
            app.processEvents()
            tabw = win.tabs
            x, y, w, h = rect(win, tabw)
            img = win.grab()
            img.copy(x, y, w, h).save(os.path.join(out, f"tab_{k}.png"))
        # warnings and pattern of the detection-limit example B
        win.sample_box.setCurrentIndex(1)
        for i, k in ((9, "warnings_B"), (2, "wp_B")):
            win.tabs.setCurrentIndex(i)
            app.processEvents()
            x, y, w, h = rect(win, win.tabs)
            hh = 330 if k == "warnings_B" else h
            win.grab().copy(x, y, w, hh).save(os.path.join(out, f"tab_{k}.png"))
        win.close()
        wizard_shots(app, out)
        print(lang, "ok", flush=True)


if __name__ == "__main__":
    main()
