# apeSees/__init__.py
"""
apeSees: A Pythonic wrapper for OpenSeesPy
==========================================
(keep your nice docstring here, trimmed if you want)
"""

from __future__ import annotations
from typing import TYPE_CHECKING

__version__ = "0.1.0"
__author__  = "Nicolas Mora Bowen"
__license__ = "MIT"
__url__     = "https://github.com/nmorabowen/apeSees"

# Expose submodules at the package level (lazy)
# Users can do: import apeSees; apeSees.timeseries
from importlib import import_module as _imp

def __getattr__(name: str):
    # Lazy module-level attributes to avoid import-time side effects
    if name == "timeseries":
        mod = _imp(".timeseries", __name__)
        globals()[name] = mod
        return mod
    if name == "materials":
        mod = _imp(".materials", __name__)
        globals()[name] = mod
        return mod
    if name == "section":
        mod = _imp(".section", __name__)
        globals()[name] = mod
        return mod
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

# Type-checking-only imports so Pylance offers completions without importing at runtime
if TYPE_CHECKING:
    from .timeseries import (
        TimeSeries,
        LinearTimeSeries,
        ConstantTimeSeries,
        PathTimeSeries,
        ASCE41Protocol,
        ModifiedATC24Protocol,
        FEMA461Protocol,
    )
    from .materials import Material, UniaxialMaterialTester
    from .section import Section, RectangularColumnSection, MomentCurvature, nAs  # ensure these exist

__all__ = [
    # Metadata
    "__version__", "__author__", "__license__", "__url__",
    # Submodules (lazy)
    "timeseries", "materials", "section",
    # Re-exported symbols (Pylance will see them via TYPE_CHECKING)
    "TimeSeries", "LinearTimeSeries", "ConstantTimeSeries", "PathTimeSeries",
    "ASCE41Protocol", "ModifiedATC24Protocol", "FEMA461Protocol",
    "Material", "UniaxialMaterialTester",
    "Section", "RectangularColumnSection", "MomentCurvature", "nAs",
]

def get_version() -> str:
    return __version__

def info() -> None:
    print(f"apeSees version {__version__}")
    print(f"Author: {__author__}")
    print(f"License: {__license__}")
    print(f"Repository: {__url__}")
    print("\nInstalled modules:")
    print("  - timeseries: Loading patterns and protocols")
    print("  - materials: Uniaxial material testing")
    print("  - section: Fiber sections and moment-curvature analysis")
    print("\nFor documentation, visit:", __url__)
