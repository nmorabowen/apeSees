"""Rectangular column section with fiber discretization."""

from __future__ import annotations
from typing import TYPE_CHECKING, Optional
from math import ceil

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle
import openseespy.opensees as ops

from .base import Section
from .functions import nAs, safe_ndiv, torsional_constant_rectangle
from .moment_curvature import MomentCurvature

if TYPE_CHECKING:
    from ..materials import Material


class RectangularColumnSection(Section):
    """
    Rectangular reinforced concrete column section with fiber discretization.
    
    Unit system: length [mm], force [N], stress [MPa].
    
    Parameters
    ----------
    B : float
        Section width [mm] (dimension along y-axis).
    H : float
        Section height [mm] (dimension along z-axis).
    cover : float
        Concrete cover thickness [mm].
    material_core : Material
        Confined concrete material (core).
    material_cover : Material
        Unconfined concrete material (cover).
    steel_material : Material
        Reinforcing steel material.
    section_tag : int
        Unique section identifier.
    number_of_rebars_along_B : int
        Number of rebars along width (y-direction).
    number_of_rebars_along_H : int
        Number of rebars along height (z-direction).
    phi : float
        Rebar diameter [mm].
    G : float
        Shear modulus [MPa].
    rebar_distance_from_edge : float, optional
        Distance from edge to rebar center [mm]. If None, calculated as cover + stirrup + phi/2.
    mesh_size : float, optional
        Target fiber mesh size [mm]. Default is 50.0.
    
    Examples
    --------
    >>> from apeSees.materials import Material
    >>> core = Material("Concrete02", 1, 30.0, 0.002, 0.0, 0.006, 0.1, 30.0, 2.0)
    >>> cover = Material("Concrete02", 2, 25.0, 0.002, 0.0, 0.004, 0.1, 25.0, 2.0)
    >>> steel = Material("Steel02", 3, 420.0, 200000.0, 0.01, 20.0, 0.925, 0.15)
    >>> 
    >>> section = RectangularColumnSection(
    ...     B=300.0, H=400.0, cover=30.0,
    ...     material_core=core, material_cover=cover, steel_material=steel,
    ...     section_tag=1, number_of_rebars_along_B=3, number_of_rebars_along_H=4,
    ...     phi=20.0, G=12500.0
    ... )
    >>> section.build()
    >>> section.plot_section()
    >>> plt.show()
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
        self.B: float = float(B)
        self.H: float = float(H)
        self.cover: float = float(cover)
        self.material_core: Material = material_core
        self.material_cover: Material = material_cover
        self.steel_material: Material = steel_material
        self.section_tag: int = int(section_tag)
        self.number_of_rebars_along_B: int = int(number_of_rebars_along_B)
        self.number_of_rebars_along_H: int = int(number_of_rebars_along_H)
        self.phi: float = float(phi)
        self.G: float = float(G)
        self.rebar_distance_from_edge: Optional[float] = rebar_distance_from_edge
        self.mesh_size: float = float(mesh_size)
        
        # Calculate section parameters
        self.rebar_array: np.ndarray = self._rebar_layout()
        
        # Composite class
        self.moment_curvature: MomentCurvature = MomentCurvature(section=self)
    
    def _rebar_layout(self) -> np.ndarray:
        """
        Calculate rebar coordinates and areas.

        Returns
        -------
        np.ndarray
            Shape (n_bars, 3) with columns [y_coord, z_coord, As] in [mm, mm, mm²].
        """
        if self.rebar_distance_from_edge is None:
            # Default: cover + stirrup diameter (assumed 10mm) + phi/2
            self.rebar_distance_from_edge = self.cover + 10.0 + self.phi / 2.0

        As_one = nAs(1, self.phi)  # mm²
        bars: list[list[float]] = []

        # Rebar positions (symmetric about center)
        z_bot = -self.H / 2.0 + self.rebar_distance_from_edge
        z_top = self.H / 2.0 - self.rebar_distance_from_edge
        y_bot = -self.B / 2.0 + self.rebar_distance_from_edge
        y_top = self.B / 2.0 - self.rebar_distance_from_edge

        y_layers = np.linspace(y_bot, y_top, self.number_of_rebars_along_B)
        z_layers = np.linspace(z_bot, z_top, self.number_of_rebars_along_H)

        # Place rebars: full rows at top/bottom, edge bars only for interior rows
        for i, y in enumerate(y_layers):
            if i == 0 or i == len(y_layers) - 1:
                # Top/bottom rows → full row
                for z in z_layers:
                    bars.append([y, z, As_one])
            else:
                # Interior rows → edge bars only
                bars.append([y, z_bot, As_one])
                bars.append([y, z_top, As_one])

        return np.asarray(bars, dtype=float)

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
    
    def build(self, verbose: bool = False) -> int:
        """
        Build fiber section in OpenSees.
        
        The section consists of:
        - Core (confined) concrete rectangle
        - Four cover (unconfined) concrete rectangles
        - Individual rebar fibers
        
        Coordinate system: y vertical, z horizontal, origin at section centroid.
        
        Parameters
        ----------
        verbose : bool, optional
            If True, prints section information. Default is False.
        
        Returns
        -------
        int
            The section tag.
        """
        y1 = self.B / 2.0
        z1 = self.H / 2.0
        cov = self.cover

        # Start fiber section with torsional stiffness
        ops.section('Fiber', self.section_tag, '-GJ', self._calculate_GJ())

        if verbose:
            print(f"Building RectangularColumnSection (tag={self.section_tag})")
            print(f"  Dimensions: B={self.B} mm, H={self.H} mm")
            print(f"  Cover: {self.cover} mm, Mesh size: {self.mesh_size} mm")
            print(f"  GJ: {self._calculate_GJ():.2e} N·mm²")

        # ---------------- Core (confined) ----------------
        yI_core, zI_core = -y1 + cov, -z1 + cov
        yJ_core, zJ_core = y1 - cov, z1 - cov
        H_core = yJ_core - yI_core
        B_core = zJ_core - zI_core
        
        if H_core > 0 and B_core > 0:
            Ny_core = safe_ndiv(H_core, self.mesh_size)
            Nz_core = safe_ndiv(B_core, self.mesh_size)
            ops.patch('rect', self.material_core.tag, Ny_core, Nz_core,
                     yI_core, zI_core, yJ_core, zJ_core)
            if verbose:
                print(f"  Core patch: {Ny_core}×{Nz_core} fibers")

        # ---------------- Cover patches ----------------
        cover_patches = [
            # Top strip: y ∈ [y1 - cov, y1], z ∈ [-z1, z1]
            (y1 - cov, -z1, y1, z1, "top"),
            # Bottom strip: y ∈ [-y1, -y1 + cov], z ∈ [-z1, z1]
            (-y1, -z1, -y1 + cov, z1, "bottom"),
            # Left strip: y ∈ [-y1 + cov, y1 - cov], z ∈ [-z1, -z1 + cov]
            (-y1 + cov, -z1, y1 - cov, -z1 + cov, "left"),
            # Right strip: y ∈ [-y1 + cov, y1 - cov], z ∈ [z1 - cov, z1]
            (-y1 + cov, z1 - cov, y1 - cov, z1, "right"),
        ]

        for yI, zI, yJ, zJ, name in cover_patches:
            H_patch = yJ - yI
            B_patch = zJ - zI
            if H_patch > 0 and B_patch > 0:
                Ny = safe_ndiv(H_patch, self.mesh_size)
                Nz = safe_ndiv(B_patch, self.mesh_size)
                ops.patch('rect', self.material_cover.tag, Ny, Nz, yI, zI, yJ, zJ)
                if verbose:
                    print(f"  Cover patch ({name}): {Ny}×{Nz} fibers")

        # ---------------- Rebars ----------------
        n_rebars = len(self.rebar_array)
        for y_coord, z_coord, As in self.rebar_array:
            ops.fiber(y_coord, z_coord, As, self.steel_material.tag)
        
        if verbose:
            print(f"  Rebars: {n_rebars} bars, φ={self.phi} mm")
            print(f"  Total steel area: {np.sum(self.rebar_array[:, 2]):.2f} mm²")

        return self.section_tag

    def plot_section(
        self,
        ax: Optional[plt.Axes] = None,
        figsize: tuple[float, float] = (6, 6),
        show_rebars: bool = True
    ) -> plt.Axes:
        """
        Plot section geometry with core, cover, and rebars.
        
        Axes convention: x-axis → y [mm], y-axis → z [mm]
        
        Parameters
        ----------
        ax : plt.Axes, optional
            Matplotlib axes. If None, creates new figure.
        figsize : tuple, optional
            Figure size in inches. Default is (6, 6).
        show_rebars : bool, optional
            Whether to show rebar locations. Default is True.
        
        Returns
        -------
        plt.Axes
            The matplotlib axes.
        """
        if ax is None:
            _, ax = plt.subplots(figsize=figsize)

        B, H, cov = self.B, self.H, self.cover
        y1, z1 = B / 2.0, H / 2.0

        # Colors
        core_color = "#b2df8a"
        cover_color = "#d9d9d9"
        steel_color = "black"
        outline_color = "black"

        # Core (confined concrete)
        core_patch = Rectangle(
            (-y1 + cov, -z1 + cov),
            B - 2 * cov,
            H - 2 * cov,
            facecolor=core_color,
            edgecolor=outline_color,
            linewidth=1.0,
            linestyle='--',
            label='Core (confined)'
        )
        ax.add_patch(core_patch)

        # Cover patches
        cover_patches = [
            Rectangle((-y1, z1 - cov), B, cov, facecolor=cover_color),  # top
            Rectangle((-y1, -z1), B, cov, facecolor=cover_color),  # bottom
            Rectangle((-y1, -z1 + cov), cov, H - 2 * cov, facecolor=cover_color),  # left
            Rectangle((y1 - cov, -z1 + cov), cov, H - 2 * cov, facecolor=cover_color),  # right
        ]
        for patch in cover_patches:
            ax.add_patch(patch)
            border = Rectangle(
                patch.get_xy(),
                patch.get_width(),
                patch.get_height(),
                edgecolor=outline_color,
                facecolor='none',
                linewidth=1.0,
                linestyle='--'
            )
            ax.add_patch(border)

        # Outer boundary
        outline = Rectangle(
            (-y1, -z1), B, H,
            edgecolor=outline_color,
            facecolor='none',
            linewidth=1.5,
            linestyle='-'
        )
        ax.add_patch(outline)

        # Rebars
        if show_rebars:
            for y, z, As in self.rebar_array:
                ax.add_patch(Circle((y, z), self.phi / 2.0, color=steel_color, zorder=10))

        # Axes settings
        ax.set_aspect('equal')
        ax.set_xlabel("y [mm]")
        ax.set_ylabel("z [mm]")
        ax.set_title(f"RC Section (tag={self.section_tag})")
        ax.grid(True, alpha=0.3)
        
        pad = max(self.phi, 0.05 * max(B, H))
        ax.set_xlim(-y1 - pad, y1 + pad)
        ax.set_ylim(-z1 - pad, z1 + pad)

        return ax

    def plot_mesh_section(
        self,
        ax: Optional[plt.Axes] = None,
        figsize: tuple[float, float] = (6, 6),
        show_rebars: bool = True,
        annotate: bool = False,
        mesh_alpha: float = 0.25,
        lw: float = 0.8,
    ) -> plt.Axes:
        """
        Plot fiber mesh layout with grid lines.
        
        Parameters
        ----------
        ax : plt.Axes, optional
            Matplotlib axes. If None, creates new figure.
        figsize : tuple, optional
            Figure size in inches.
        show_rebars : bool, optional
            Whether to show rebars. Default is True.
        annotate : bool, optional
            Whether to annotate mesh divisions. Default is False.
        mesh_alpha : float, optional
            Transparency of mesh patches. Default is 0.25.
        lw : float, optional
            Line width for grid. Default is 0.8.
        
        Returns
        -------
        plt.Axes
            The matplotlib axes.
        """
        if ax is None:
            _, ax = plt.subplots(figsize=figsize)

        y1, z1 = self.B / 2.0, self.H / 2.0
        cov = self.cover

        # Colors
        core_fill = "#b2df8a"
        cover_fill = "#d9d9d9"
        outline_color = "black"
        grid_color = "black"

        # Define patches: (yI, zI, yJ, zJ, kind)
        patches = []
        # Core
        yI_core, zI_core = -y1 + cov, -z1 + cov
        yJ_core, zJ_core = y1 - cov, z1 - cov
        patches.append((yI_core, zI_core, yJ_core, zJ_core, "core"))
        
        # Covers
        patches += [
            (y1 - cov, -z1, y1, z1, "cover"),  # top
            (-y1, -z1, -y1 + cov, z1, "cover"),  # bottom
            (-y1 + cov, -z1, y1 - cov, -z1 + cov, "cover"),  # left
            (-y1 + cov, z1 - cov, y1 - cov, z1, "cover"),  # right
        ]

        # Outer boundary
        ax.add_patch(Rectangle(
            (-y1, -z1), self.B, self.H,
            edgecolor=outline_color, facecolor='none',
            linewidth=lw, linestyle='--'
        ))

        # Draw patches with mesh
        for (yI, zI, yJ, zJ, kind) in patches:
            Hpatch, Bpatch = (yJ - yI), (zJ - zI)
            if Hpatch <= 0 or Bpatch <= 0:
                continue
            
            Ny = safe_ndiv(Hpatch, self.mesh_size)
            Nz = safe_ndiv(Bpatch, self.mesh_size)

            color = core_fill if kind == "core" else cover_fill
            
            # Fill patch
            ax.add_patch(Rectangle(
                (yI, zI), Hpatch, Bpatch,
                facecolor=color, alpha=mesh_alpha,
                edgecolor='none'
            ))

            # Draw grid
            dy, dz = Hpatch / Ny, Bpatch / Nz
            # Vertical lines (constant y)
            for i in range(1, Ny):
                y = yI + i * dy
                ax.plot([y, y], [zI, zJ], color=grid_color, lw=lw, ls=':')
            # Horizontal lines (constant z)
            for j in range(1, Nz):
                z = zI + j * dz
                ax.plot([yI, yJ], [z, z], color=grid_color, lw=lw, ls=':')

            # Perimeter
            ax.add_patch(Rectangle(
                (yI, zI), Hpatch, Bpatch,
                facecolor='none', edgecolor=grid_color,
                lw=lw, linestyle='--'
            ))

            # Annotation
            if annotate:
                ax.text((yI + yJ) / 2, (zI + zJ) / 2, f"{Ny}×{Nz}",
                       ha='center', va='center', fontsize=8, color='black')

        # Rebars
        if show_rebars:
            for y, z, As in self.rebar_array:
                ax.add_patch(Circle((y, z), self.phi / 2.0, color='black', lw=0.5, zorder=10))

        # Axes settings
        ax.set_aspect("equal")
        ax.set_xlabel("y [mm]")
        ax.set_ylabel("z [mm]")
        ax.set_title(f"Fiber Mesh Layout (Section {self.section_tag})")
        
        pad = max(self.phi, 0.02 * max(self.B, self.H))
        ax.set_xlim(-y1 - pad, y1 + pad)
        ax.set_ylim(-z1 - pad, z1 + pad)
        ax.grid(False)

        return ax
    
    def __repr__(self) -> str:
        return (
            f"RectangularColumnSection(tag={self.section_tag}, "
            f"B={self.B}, H={self.H}, cover={self.cover}, "
            f"rebars={len(self.rebar_array)})"
        )