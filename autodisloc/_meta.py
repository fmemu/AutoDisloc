# SPDX-License-Identifier: MIT
# AutoDisloc 2 - Copyright (c) 2026 Firat Memu
"""Program identity. Files the program produces for the user (figures, Excel
reports, LaTeX tables, instrument models) record only the program name and
version (``software()`` / ``stamp()``); the author appears only in the
program's own identity (About dialog, licence, package metadata)."""

NAME = "AutoDisloc"
VERSION = "2.0.0"
AUTHOR = "Fırat Memu"
LICENSE = "MIT"
COPYRIGHT = f"Copyright (c) 2026 {AUTHOR}"
URL = "https://github.com/fmemu/AutoDisloc"


def software():
    """Program name and version, e.g. 'AutoDisloc 2.0.0'."""
    return f"{NAME} {VERSION}"


def stamp():
    """Dictionary stored in produced data files (instrument models)."""
    return {"software": software(), "license": LICENSE}
