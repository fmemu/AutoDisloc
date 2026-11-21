# SPDX-License-Identifier: MIT
# AutoDisloc 2 - Copyright (c) 2026 Firat Memu
"""Material presets for titanium alloys.

The analysis (Dragomir-Ungar contrast factors of the hexagonal slip systems,
elastic constants, Burgers vectors) is that of alpha / alpha' titanium. A
preset only supplies the nominal lattice parameters used to place the
peak-fit windows and whether a beta phase is expected; the lattice
parameters themselves are always measured (Cohen least squares). With
``refine_nominal`` (default) nominal values that are clearly off (more than
0.35 deg at an alpha reflection) are replaced by values adjusted to the
measured peak positions, so any alpha-Ti alloy can start from either preset.
"""

from dataclasses import dataclass

from . import ti64


@dataclass(frozen=True)
class Material:
    key: str
    name: str
    a: float          # alpha a, Angstrom
    c: float          # alpha c
    a_beta: float     # beta (bcc) a
    beta: str         # "auto": beta reflections modelled when present, "no": not modelled
    source: str


MATERIALS = {
    "Ti-6Al-4V": Material("Ti-6Al-4V", "Ti-6Al-4V (α/α′ + β)", ti64.ALPHA_A, ti64.ALPHA_C, ti64.BETA_A, "auto",
                          "nominal values of this work; α′ martensite and α + β"),
    "CP-Ti": Material("CP-Ti", "CP-Ti, grade 1–4 (α)", 2.9505, 4.6826, 3.30, "no",
                      "α-Ti, ICDD PDF 00-044-1294; no β phase expected"),
    "custom": Material("custom", "custom α-Ti alloy", ti64.ALPHA_A, ti64.ALPHA_C, ti64.BETA_A, "auto",
                       "user values"),
}
MATERIAL_KEYS = list(MATERIALS)


def get(key):
    return MATERIALS.get(key, MATERIALS["Ti-6Al-4V"])


def display_name(key):
    """Localised name (falls back to the table value)."""
    from .i18n import tr
    t = tr("mat.name." + key)
    return get(key).name if t == "mat.name." + key else t


def display_source(key):
    from .i18n import tr
    t = tr("mat.src." + key)
    return get(key).source if t == "mat.src." + key else t
