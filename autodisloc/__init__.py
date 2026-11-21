# SPDX-License-Identifier: MIT
# AutoDisloc 2 - Copyright (c) 2026 Firat Memu
"""AutoDisloc: XRD dislocation density of hcp alpha/alpha' Ti-6Al-4V by the
modified Williamson-Hall, modified Warren-Averbach and Wilkens whole-profile
methods.

Validation:           docs/validation.md
Whitepaper:           docs/whitepaper/
"""

from ._meta import AUTHOR as __author__, LICENSE as __license__, VERSION as __version__

from .i18n import get_language, set_language, tr
from .io import read_pattern, Pattern
from .instrument import InstrumentModel, fit_instrument
from .pipeline import analyze, AnalysisOptions, AnalysisResult

__all__ = [
    "read_pattern", "Pattern",
    "InstrumentModel", "fit_instrument",
    "analyze", "AnalysisOptions", "AnalysisResult",
    "get_language", "set_language", "tr",
]
