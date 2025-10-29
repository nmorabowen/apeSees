"""
apeSees: A Pythonic wrapper for OpenSeesPy
============================================

apeSees provides an intuitive, object-oriented interface for OpenSeesPy with 
helpful utilities for structural analysis and visualization.

Modules
-------
timeseries
    Time series definitions for loading patterns (Linear, Constant, Path, 
    ASCE-41, Modified ATC-24, FEMA-461 protocols).
    
materials
    Uniaxial material definitions with built-in testing capabilities 
    (cyclic response, backbone curves, hysteretic behavior).
    
section
    Fiber section definitions with moment-curvature analysis 
    (rectangular columns, fiber visualization, M-κ diagrams).

Quick Start
-----------
>>> from apeSees.materials import Material
>>> from apeSees.timeseries import ASCE41Protocol
>>> import matplotlib.pyplot as plt
>>> 
>>> # Create a steel material
>>> steel = Material("Steel02", 1, 420.0, 200000.0, 0.01, 20.0, 0.925, 0.15)
>>> 
>>> # Test with ASCE-41 cyclic protocol
>>> ax, result = steel.cyclic_tester(max_strain=0.02)
>>> plt.show()
>>> 
>>> # Access results
>>> print(f"Peak stress: {result.peak_stress:.2f} MPa")
>>> print(f"Energy dissipated: {result.energy_dissipated:.2e} J")

Examples
--------
Material Testing:
    >>> steel = Material("Steel02", 1, 420.0, 200000.0, 0.01, 20.0, 0.925, 0.15)
    >>> ax, result = steel.backbone_tester(max_strain=0.03)
    >>> plt.show()

Section Analysis:
    >>> from apeSees.section import RectangularColumnSection
    >>> section = RectangularColumnSection(
    ...     B=300.0, H=400.0, cover=30.0,
    ...     material_core=core, material_cover=cover, steel_material=steel,
    ...     section_tag=1, number_of_rebars_along_B=3, number_of_rebars_along_H=4,
    ...     phi=20.0, G=12500.0
    ... )
    >>> ax, result = section.moment_curvature.plot(axial_load=-1e6)
    >>> plt.show()

Loading Protocols:
    >>> from apeSees.timeseries import FEMA461Protocol
    >>> protocol = FEMA461Protocol(tag=1, max_disp=0.02, alpha=0.62)
    >>> protocol.plot()
    >>> plt.show()

Notes
-----
- All length units are in millimeters [mm]
- All force units are in Newtons [N]
- All stress units are in Megapascals [MPa]
- Compression is negative, tension is positive

Author: nmorabowenl
License: MIT
Repository: https://github.com/nmorabowen/apeSees
"""

__version__ = "0.1.0"
__author__ = "Nicolas Mora Bowen"
__license__ = "MIT"
__url__ = "https://github.com/nmorabowen/apeSees"

# Import main modules for convenient access
from . import timeseries
from . import materials
from . import section

# Expose commonly used classes at package level
from .timeseries import (
    TimeSeries,
    LinearTimeSeries,
    ConstantTimeSeries,
    PathTimeSeries,
    ASCE41Protocol,
    ModifiedATC24Protocol,
    FEMA461Protocol,
)

from .materials import (
    Material,
    UniaxialMaterialTester,
)

from .section import (
    Section,
    RectangularColumnSection,
    MomentCurvature,
    nAs,
)

__all__ = [
    # Metadata
    "__version__",
    "__author__",
    "__license__",
    "__url__",
    
    # Modules
    "timeseries",
    "materials",
    "section",
    
    # Time series
    "TimeSeries",
    "LinearTimeSeries",
    "ConstantTimeSeries",
    "PathTimeSeries",
    "ASCE41Protocol",
    "ModifiedATC24Protocol",
    "FEMA461Protocol",
    
    # Materials
    "Material",
    "UniaxialMaterialTester",
    
    # Sections
    "Section",
    "RectangularColumnSection",
    "MomentCurvature",
    "nAs",
]


def get_version() -> str:
    """
    Get the current version of apeSees.
    
    Returns
    -------
    str
        Version string.
    """
    return __version__


def info() -> None:
    """
    Print package information.
    """
    print(f"apeSees version {__version__}")
    print(f"Author: {__author__}")
    print(f"License: {__license__}")
    print(f"Repository: {__url__}")
    print("\nInstalled modules:")
    print("  - timeseries: Loading patterns and protocols")
    print("  - materials: Uniaxial material testing")
    print("  - section: Fiber sections and moment-curvature analysis")
    print("\nFor documentation, visit: https://github.com/nmorabowen/apeSees")