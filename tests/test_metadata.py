# SPDX-License-Identifier: MIT
# AutoDisloc 2 - Copyright (c) 2026 Firat Memu
"""Zenodo uses only .zenodo.json when it exists and ignores CITATION.cff, so the
two files (and the program version) must not drift apart."""
import json
import os
import re
import sys

ROOT = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, ROOT)

from autodisloc._meta import AUTHOR, LICENSE, VERSION  # noqa: E402


def _cff():
    text = open(os.path.join(ROOT, "CITATION.cff"), encoding="utf-8").read()
    top = text.split("\nreferences:")[0]           # the thesis reference has its own title/authors
    get = lambda key: re.search(rf"^{key}:\s*\"?([^\"#\n]+?)\"?\s*(#.*)?$", top, re.M).group(1).strip()
    orcid = re.search(r"^\s+orcid:\s*\"?([^\"#\n]+)", top, re.M)
    return {"title": get("title"), "version": get("version"), "license": get("license"),
            "family": re.search(r"family-names:\s*(.+)", top).group(1).strip(),
            "given": re.search(r"given-names:\s*(.+)", top).group(1).strip(),
            "orcid": orcid.group(1).strip() if orcid else None,
            "keywords": re.findall(r"^  - (.+)$", top.split("keywords:")[1], re.M)}


def test_citation_files_agree():
    c = _cff()
    z = json.load(open(os.path.join(ROOT, ".zenodo.json"), encoding="utf-8"))
    assert z["title"] == c["title"]
    assert z["version"] == c["version"] == VERSION
    assert z["license"].lower() == c["license"].lower() == LICENSE.lower()
    assert z["creators"][0]["name"] == f"{c['family']}, {c['given']}"
    assert f"{c['given']} {c['family']}" == AUTHOR
    assert z["creators"][0].get("orcid") == (c["orcid"].rsplit("/", 1)[-1] if c["orcid"] else None)
    assert z["keywords"] == c["keywords"]


def test_license_file_is_mit():
    text = open(os.path.join(ROOT, "LICENSE"), encoding="utf-8").read()
    assert text.startswith("MIT License") and f"Copyright (c) 2026 {AUTHOR}" in text
    assert "Permission is hereby granted, free of charge" in text


def test_version_is_the_same_everywhere():
    pyproject = open(os.path.join(ROOT, "pyproject.toml"), encoding="utf-8").read()
    spec = open(os.path.join(ROOT, "packaging", "AutoDisloc2.spec"), encoding="utf-8").read()
    assert re.search(r'^version = "([^"]+)"', pyproject, re.M).group(1) == VERSION
    assert re.search(r'"CFBundleShortVersionString": "([^"]+)"', spec).group(1) == VERSION


# ---------------------------------------------------------------------------
# Files produced for the user record the program name and version only: no
# author and no hidden marks (figures, Excel report, LaTeX/CSV, instrument JSON).
FORBIDDEN = [b"Memu", b"Firat", "Fırat".encode("utf-8"), b"fm-2026", b"provenance",
             b"QXV0b0Rpc2xvYyB8", b"_about"]


def _payload(path):
    """Raw bytes plus every decompressed part (xlsx members, PDF streams)."""
    import zipfile
    import zlib
    data = open(path, "rb").read()
    parts = [data]
    if zipfile.is_zipfile(path):
        with zipfile.ZipFile(path) as z:
            parts += [z.read(n) for n in z.namelist()]
    if path.endswith(".pdf"):
        for m in re.finditer(rb"stream\r?\n(.*?)endstream", data, re.S):
            try:
                parts.append(zlib.decompress(m.group(1)))
            except zlib.error:
                pass
    return parts


def test_outputs_contain_no_author_and_no_hidden_marks(tmp_path):
    from autodisloc._meta import software
    from autodisloc.export import export_package
    from autodisloc.i18n import set_language
    from autodisloc.instrument import InstrumentModel
    from autodisloc.io import read_pattern
    from autodisloc.pipeline import AnalysisOptions, analyze
    set_language("en")
    inst = InstrumentModel.load(os.path.join(ROOT, "autodisloc", "data", "instrument_corundum_example.json"))
    res = analyze(read_pattern(os.path.join(ROOT, "examples", "synthetic_Ti64_A.xy")), inst, "A",
                  AnalysisOptions(whole_profile=False, mc_draws=0))
    out = tmp_path / "pkg"
    export_package([res], str(out), inst)
    inst.save(str(tmp_path / "inst.json"))
    files = [os.path.join(d, f) for d, _, fs in os.walk(tmp_path) for f in fs]
    exts = {os.path.splitext(f)[1] for f in files}
    assert {".png", ".pdf", ".svg", ".tif", ".xlsx", ".tex", ".csv", ".json"} <= exts
    for f in files:
        for part in _payload(f):
            for bad in FORBIDDEN:
                assert bad not in part, (f, bad)
    # what is recorded instead: program name and version
    soft = software()
    assert soft == f"AutoDisloc {VERSION}"
    from PIL import Image
    png = next(f for f in files if f.endswith(".png"))
    assert Image.open(png).info.get("Software") == soft
    tif = next(f for f in files if f.endswith(".tif"))
    assert Image.open(tif).tag_v2.get(305) == soft
    import openpyxl
    wb = openpyxl.load_workbook(next(f for f in files if f.endswith(".xlsx")))
    assert wb.properties.creator == soft
    assert all(ws.sheet_state == "visible" for ws in wb.worksheets)
    tex = next(f for f in files if f.endswith(".tex"))
    assert open(tex, encoding="utf-8").read().startswith(f"% {soft}\n\\begin")
    gen = json.load(open(tmp_path / "inst.json", encoding="utf-8"))["_generator"]
    assert gen == {"software": soft, "license": LICENSE}


def test_example_instrument_model_has_the_new_stamp():
    d = json.load(open(os.path.join(ROOT, "autodisloc", "data", "instrument_corundum_example.json"),
                       encoding="utf-8"))
    assert d["_generator"] == {"software": f"AutoDisloc {VERSION}", "license": LICENSE}
