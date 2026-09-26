from __future__ import annotations
from typing import TYPE_CHECKING, Optional

from dataclasses import dataclass
import numpy as np
import matplotlib.pyplot as plt

# --- MODIFIED IMPORTS ---
from .general_fiber_section import GeneralFiberSection, PatchDefinition
from .functions import safe_ndiv, torsional_constant_rectangle
from .moment_curvature import MomentCurvature
from .fiber_mapper import FiberMapper

if TYPE_CHECKING:
    from ..materials import Material
    from .moment_curvature import MomentCurvature
    from .fiber_mapper import FiberMapper


# order=True keeps the <, <=, >, >= methods that attr.dataclass generated.
@dataclass(order=True)
class SectionProperties:
    """Section geometric properties for a solid section."""
    
    A_g: float        # Gross area [mm²]
    I_y: float        # Moment of inertia about y-axis [mm^4]
    I_z: float        # Moment of inertia about z-axis [mm^4]
    S_y: float        # Section modulus about y-axis [mm^3]
    S_z: float        # Section modulus about z-axis [mm^3]
    r_y: float        # Radius of gyration about y-axis [mm]
    r_z: float        # Radius of gyration about z-axis [mm]

    @classmethod
    def from_section(cls, section: "RectangularSolidSection") -> SectionProperties:
        """
        Calculate and instantiate properties from a RectangularSolidSection.
        """
        B, H = section.B, section.H
        
        # --- Gross Section Properties ---
        A_g = B * H
        I_y = (B * H**3) / 12.0
        I_z = (H * B**3) / 12.0
        
        # --- Derived Geometric Properties (Gross) ---
        S_y = I_y / (H / 2.0) if H > 0 else 0.0
        S_z = I_z / (B / 2.0) if B > 0 else 0.0
        r_y = (I_y / A_g)**0.5 if A_g > 0 else 0.0
        r_z = (I_z / A_g)**0.5 if A_g > 0 else 0.0
        
        return cls(
            A_g=A_g,
            I_y=I_y,
            I_z=I_z,
            S_y=S_y,
            S_z=S_z,
            r_y=r_y,
            r_z=r_z,
        )

# --- MODIFIED CLASS DEFINITION ---
class RectangularSolidSection(GeneralFiberSection):
    """
    Rectangular solid section with fiber discretization.
    
    This is a high-level wrapper that creates a GeneralFiberSection.
    
    Parameters
    ----------
    B : float
        Section width (dimension along y-axis).
    H : float
        Section height (dimension along z-axis).
    material : Material
        Material for the solid section.
    section_tag : int
        Unique section identifier.
    G : float
        Shear modulus.
    mesh_size : float, optional
        Target fiber mesh size. Default is 50.0.
    """
    
    def __init__(
        self,
        B: float,
        H: float,
        material: Material,
        section_tag: int,
        G: float,
        mesh_size: float = 50.0
    ):
        self.B: float = float(B)
        self.H: float = float(H)
        self.material: Material = material
        self.G: float = float(G)
        self.mesh_size: float = float(mesh_size)
        
        # --- 1. Define Geometry for the Parent Class ---
        y1 = self.B / 2.0
        z1 = self.H / 2.0
        
        # Calculate fiber divisions
        Ny_patch = safe_ndiv(self.B, self.mesh_size)
        Nz_patch = safe_ndiv(self.H, self.mesh_size)
        
        # Create the single patch definition
        solid_patch = PatchDefinition(
            material=self.material,
            num_fibers_y=Ny_patch,
            num_fibers_z=Nz_patch,
            coords=[-y1, -z1, y1, z1],
            type='rect'
        )
        
        # --- 2. Calculate Torsional Stiffness ---
        GJ = self._calculate_GJ()
        
        # --- 3. Call Parent __init__ ---
        super().__init__(
            section_tag=int(section_tag),
            patches=[solid_patch],
            fibers=[],  # No individual fibers
            GJ=GJ
        )
        
        # --- 4. Add properties and composite classes ---
        self.properties: SectionProperties = SectionProperties.from_section(self)
        self.moment_curvature: MomentCurvature = MomentCurvature(section=self)
        
        # --- THIS IS THE FIX ---
        self.fiber_map: FiberMapper = FiberMapper(section=self)
        # --- END FIX ---

    def _calculate_GJ(self) -> float:
        """
        Calculate torsional stiffness GJ.
        
        Returns
        -------
        float
            GJ [N·mm²].
        """
        J = torsional_constant_rectangle(self.B, self.H)
        return self.G * J
    
    def __repr__(self) -> str:
        # Keep the specific __repr__
        return (
            f"RectEnglishSolidSection(tag={self.section_tag}, "
            f"B={self.B}, H={self.H})"
        )