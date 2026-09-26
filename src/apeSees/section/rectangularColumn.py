from __future__ import annotations
from typing import TYPE_CHECKING, Optional

from dataclasses import dataclass
import numpy as np
import openseespy.opensees as ops # Keep ops for 'nAs' call? No, that's from .functions

# --- MODIFIED IMPORTS ---
from .general_fiber_section import GeneralFiberSection, PatchDefinition, FiberDefinition
from .functions import nAs, safe_ndiv, torsional_constant_rectangle
from .moment_curvature import MomentCurvature
from .neural_moment_curvature_trainer import NeuralMomentCurvatureTrainer
from .fiber_mapper import FiberMapper

if TYPE_CHECKING:
    from ..materials import Material
    from .moment_curvature import MomentCurvature
    from .neural_moment_curvature_trainer import NeuralMomentCurvatureTrainer
    from .fiber_mapper import FiberMapper
    from .rectangularColumn import RectangularColumnSection 

# order=True keeps the <, <=, >, >= methods that attr.dataclass generated.
@dataclass(order=True)
class SectionProperties:
    """Section geometric and reinforcement properties."""
    
    A_g: float        # Gross area [mm²]
    A_c: float        # Concrete area [mm²]
    A_s: float        # Total steel area [mm²]
    I_y: float        # Moment of inertia about y-axis [mm^4]
    I_z: float        # Moment of inertia about z-axis [mm^4]
    S_y: float        # Section modulus about y-axis [mm^3]
    S_z: float        # Section modulus about z-axis [mm^3]
    r_y: float        # Radius of gyration about y-axis [mm]
    r_z: float        # Radius of gyration about z-axis [mm]
    rho_l: float      # Longitudinal reinforcement ratio

    @classmethod
    def from_section(cls, section: RectangularColumnSection) -> SectionProperties:
        """
        Calculate and instantiate properties from a RectangularColumnSection.
        """
        B, H, cover = section.B, section.H, section.cover
        
        A_g = B * H
        I_y = (B * H**3) / 12.0
        I_z = (H * B**3) / 12.0
        
        A_s = np.sum(section.rebar_array[:, 2])
        
        # Note: This Ac is not quite right, but we'll keep it for consistency
        A_c = A_g - (B-2*cover)*(H-2*cover)
        rho_l = A_s / A_g if A_g > 0 else 0.0
        
        S_y = I_y / (H / 2.0) if H > 0 else 0.0
        S_z = I_z / (B / 2.0) if B > 0 else 0.0
        r_y = (I_y / A_g)**0.5 if A_g > 0 else 0.0
        r_z = (I_z / A_g)**0.5 if A_g > 0 else 0.0
        
        return cls(
            A_g=A_g,
            A_c=A_c,
            A_s=A_s,
            I_y=I_y,
            I_z=I_z,
            S_y=S_y,
            S_z=S_z,
            r_y=r_y,
            r_z=r_z,
            rho_l=rho_l
        )

# --- MODIFIED CLASS DEFINITION ---
class RectangularColumnSection(GeneralFiberSection):
    """
    Rectangular reinforced concrete column section with fiber discretization.
    
    This is a high-level wrapper that creates a GeneralFiberSection.
    """
    
    def __init__(
        self,
        B: float,
        H: float,
        cover: float,
        material_core: Material,
        material_cover: Material,
        steel_material: Material,
        section_tag: int,
        number_of_rebars_along_B: int,
        number_of_rebars_along_H: int,
        phi: float,
        G: float,
        rebar_distance_from_edge: Optional[float] = None,
        mesh_size: float = 50.0
    ):
        # --- 1. Set all self attributes ---
        self.B: float = float(B)
        self.H: float = float(H)
        self.cover: float = float(cover)
        self.material_core: Material = material_core
        self.material_cover: Material = material_cover
        self.steel_material: Material = steel_material
        # section_tag is passed to super()
        self.number_of_rebars_along_B: int = int(number_of_rebars_along_B)
        self.number_of_rebars_along_H: int = int(number_of_rebars_along_H)
        self.phi: float = float(phi)
        self.G: float = float(G)
        self.rebar_distance_from_edge: Optional[float] = rebar_distance_from_edge
        self.mesh_size: float = float(mesh_size)
        
        # --- 2. Call helper methods ---
        self.rebar_array: np.ndarray = self._rebar_layout()
        GJ: float = self._calculate_GJ()
        
        # --- 3. Generate PatchDefinitions (from old build() method) ---
        patches: list[PatchDefinition] = []
        y1 = self.B / 2.0
        z1 = self.H / 2.0
        cov = self.cover

        # Core (confined)
        yI_core, zI_core = -y1 + cov, -z1 + cov
        yJ_core, zJ_core = y1 - cov, z1 - cov
        H_core = yJ_core - yI_core
        B_core = zJ_core - zI_core
        
        if H_core > 0 and B_core > 0:
            Ny_core = safe_ndiv(H_core, self.mesh_size)
            Nz_core = safe_ndiv(B_core, self.mesh_size)
            patches.append(PatchDefinition(
                material=self.material_core,
                num_fibers_y=Ny_core,
                num_fibers_z=Nz_core,
                coords=[yI_core, zI_core, yJ_core, zJ_core],
                type='rect'
            ))

        # Cover patches
        cover_patch_coords = [
            (y1 - cov, -z1, y1, z1),      # top
            (-y1, -z1, -y1 + cov, z1),  # bottom
            (-y1 + cov, -z1, y1 - cov, -z1 + cov), # left
            (-y1 + cov, z1 - cov, y1 - cov, z1), # right
        ]
        
        for yI, zI, yJ, zJ in cover_patch_coords:
            H_patch = yJ - yI
            B_patch = zJ - zI
            if H_patch > 0 and B_patch > 0:
                Ny = safe_ndiv(H_patch, self.mesh_size)
                Nz = safe_ndiv(B_patch, self.mesh_size)
                patches.append(PatchDefinition(
                    material=self.material_cover,
                    num_fibers_y=Ny,
                    num_fibers_z=Nz,
                    coords=[yI, zI, yJ, zJ],
                    type='rect'
                ))
        
        # --- 4. Generate FiberDefinitions ---
        fibers: list[FiberDefinition] = []
        for y_coord, z_coord, As in self.rebar_array:
            fibers.append(FiberDefinition(
                y=y_coord,
                z=z_coord,
                area=As,
                material=self.steel_material
            ))
        
        # --- 5. Call Parent __init__ ---
        super().__init__(
            section_tag=int(section_tag),
            patches=patches,
            fibers=fibers,
            GJ=GJ
        )
        
        # --- 6. Add properties and composite classes ---
        self.properties: SectionProperties = SectionProperties.from_section(self)
        self.moment_curvature: MomentCurvature = MomentCurvature(section=self)
        self.neural_moment_curvature_trainer: NeuralMomentCurvatureTrainer = NeuralMomentCurvatureTrainer(section=self)
        self.fiber_map: FiberMapper = FiberMapper(section=self)
    
    def _rebar_layout(self) -> np.ndarray:
        """
        Calculate rebar coordinates and areas. (Unchanged)
        """
        if self.rebar_distance_from_edge is None:
            # Default: cover + stirrup diameter (assumed 10mm) + phi/2
            self.rebar_distance_from_edge = self.cover + 10.0 + self.phi / 2.0

        As_one = nAs(1, self.phi)  # mm²
        bars: list[list[float]] = []

        z_bot = -self.H / 2.0 + self.rebar_distance_from_edge
        z_top = self.H / 2.0 - self.rebar_distance_from_edge
        y_bot = -self.B / 2.0 + self.rebar_distance_from_edge
        y_top = self.B / 2.0 - self.rebar_distance_from_edge

        y_layers = np.linspace(y_bot, y_top, self.number_of_rebars_along_B)
        z_layers = np.linspace(z_bot, z_top, self.number_of_rebars_along_H)

        for i, y in enumerate(y_layers):
            if i == 0 or i == len(y_layers) - 1:
                for z in z_layers:
                    bars.append([y, z, As_one])
            else:
                bars.append([y, z_bot, As_one])
                bars.append([y, z_top, As_one])

        return np.asarray(bars, dtype=float)

    def _calculate_GJ(self) -> float:
        """
        Calculate torsional stiffness GJ. (Unchanged)
        """
        J = torsional_constant_rectangle(self.B, self.H)
        return self.G * J
    
    # --- build() method is DELETED ---
    # The parent GeneralFiberSection.build() is now used.

    # --- plot_section() method is DELETED ---
    # The parent GeneralFileSection.plot_section() is used.
    # For a color-coded plot, use self.fiber_map.plot()

    # --- plot_mesh_section() method is DELETED ---

    def __repr__(self) -> str:
        return (
            f"RectangularColumnSection(tag={self.section_tag}, "
            f"B={self.B}, H={self.H}, cover={self.cover}, "
            f"rebars={len(self.rebar_array)})"
        )