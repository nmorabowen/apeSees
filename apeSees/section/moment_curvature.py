"""Moment-curvature analysis for fiber sections."""

from __future__ import annotations
from typing import TYPE_CHECKING, Optional, Tuple

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle
import openseespy.opensees as ops

from .results import MomentCurvatureResults
from ..timeseries import LinearTimeSeries, ASCE41Protocol

if TYPE_CHECKING:
    from .base import Section
    from ..timeseries import TimeSeries


class MomentCurvature:
    """
    Moment-curvature analysis using a 2-node zeroLengthSection element.
    
    This class is designed to be used as a composite within a Section object.
    
    Parameters
    ----------
    section : Section
        The fiber section to analyze.
    
    Examples
    --------
    >>> from apeSees.section import RectangularColumnSection
    >>> # ... create section ...
    >>> mc = section.moment_curvature
    >>> result = mc.solve(axial_load=-1000000.0, max_curvature=0.004)
    >>> result.plot()
    >>> plt.show()
    """
    
    def __init__(self, section: Section):
        self.section: Section = section
    
    def solve(
        self,
        axial_load: float = 0.0,
        number_of_points: int = 100,
        max_curvature: float = 0.004,
        number_of_iterations: int = 200,
        theta: float = 0.0,
        *,
        use_protocol: bool = False,
        protocol: Optional[TimeSeries] = None,
    ) -> MomentCurvatureResults:
        """
        Run moment-curvature analysis.
        
        Parameters
        ----------
        axial_load : float, optional
            Applied axial load [N]. Compression is negative. Default is 0.0.
        number_of_points : int, optional
            Number of analysis steps. Default is 100.
        max_curvature : float, optional
            Maximum target curvature [1/mm]. Default is 0.004.
        number_of_iterations : int, optional
            Maximum iterations per step. Default is 200.
        theta : float, optional
            Section rotation angle [degrees]. Default is 0.0.
        use_protocol : bool, optional
            If True and protocol is provided, use cyclic protocol. Default is False.
        protocol : TimeSeries, optional
            Custom loading protocol. If None and use_protocol=True, uses ASCE41.
        
        Returns
        -------
        MomentCurvatureResults
            Analysis results containing curvature, moment, and fiber history.
        
        Examples
        --------
        >>> result = mc.solve(axial_load=-1e6, max_curvature=0.005, number_of_points=200)
        >>> print(f"Peak moment: {result.peak_moment:.2e} N·mm")
        
        >>> # Cyclic analysis
        >>> from apeSees.timeseries import ASCE41Protocol
        >>> protocol = ASCE41Protocol(tag=1, max_disp=1.0)
        >>> result = mc.solve(axial_load=-1e6, use_protocol=True, protocol=protocol)
        """
        
        ops.wipe()
        ops.model('basic', '-ndm', 3, '-ndf', 6)

        # Nodes
        BC_node = 1
        load_node = 2
        ops.node(BC_node, 0.0, 0.0, 0.0)
        ops.node(load_node, 0.0, 0.0, 0.0)

        # Boundary conditions
        ops.fix(BC_node, *[1, 1, 1, 1, 1, 1])
        ops.fix(load_node, *[0, 1, 1, 1, 0, 1])  # ux & rz free

        # Build materials
        self.section.material_core.build()
        self.section.material_cover.build()
        self.section.steel_material.build()

        # Build section
        section_tag = self.section.build()

        # Element with rotation
        element_tag = 200
        theta_rad = np.radians(theta)
        ops.element('zeroLengthSection',
                   element_tag,
                   BC_node, load_node,
                   section_tag,
                   '-orient', 1.0, 0.0, 0.0,  # x-axis
                             0.0, -np.cos(theta_rad), np.sin(theta_rad))  # y-axis

        # Fiber recorder
        ops.recorder('Element', '-time',
                    '-file', 'fiberData.out',
                    '-ele', element_tag,
                    'section', 'fiberData')

        # Apply axial load
        ts_ax = 500
        ops.timeSeries('Constant', ts_ax)
        pat_ax = 600
        ops.pattern('Plain', pat_ax, ts_ax)
        ops.load(load_node, axial_load, 0, 0, 0, 0, 0)

        # Analysis setup for axial load
        ops.integrator('LoadControl', 0.0)
        ops.system('SuperLU')
        ops.test('NormUnbalance', 1e-6, number_of_iterations, 0)
        ops.numberer('Plain')
        ops.constraints('Transformation')
        ops.algorithm('KrylovNewton')
        ops.analysis('Static')
        ops.analyze(1)

        # Moment-curvature time series
        timeseries_tag = 501
        if use_protocol and protocol is not None:
            protocol.build()
            timeseries_tag = protocol.tag
        elif use_protocol:
            # Default to ASCE41 if use_protocol is True but no protocol provided
            ASCE41Protocol(tag=timeseries_tag, max_disp=1.0).build()
        else:
            LinearTimeSeries(timeseries_tag, factor=1.0).build()

        # Apply moment-curvature pattern
        pat_mc = 601
        ops.pattern('Plain', pat_mc, timeseries_tag)
        ops.sp(load_node, 5, max_curvature)  # DOF 5 = rotation z

        # Integrator
        dκ = 1.0 / number_of_points
        ops.integrator('LoadControl', dκ)

        # Initialize result arrays
        n_steps = number_of_points + 1
        curvatures = np.zeros(n_steps)
        moments = np.zeros(n_steps)

        # Probe fiber count
        probe = ops.eleResponse(element_tag, 'section', 'fiberData2')
        n_fib = len(probe) // 6
        fiber_history = np.zeros((n_steps, n_fib, 6))
        fiber_history[0, :, :] = np.array(probe, dtype=float).reshape(-1, 6)

        # Run analysis
        converged = True
        for i in range(n_steps):
            curvatures[i] = ops.nodeDisp(load_node, 5)
            moments[i] = ops.eleForce(element_tag, 5)  # Moment at node (reaction)
            
            fdat = np.array(ops.eleResponse(element_tag, 'section', 'fiberData2'), dtype=float)
            fiber_history[i, :, :] = fdat.reshape(-1, 6)
            
            if i < n_steps - 1:
                if ops.analyze(1) != 0:
                    converged = False
                    # Truncate arrays
                    curvatures = curvatures[:i+1]
                    moments = moments[:i+1]
                    fiber_history = fiber_history[:i+1, :, :]
                    break

        ops.wipe()
        
        return MomentCurvatureResults(
            axial_load=axial_load,
            curvatures=curvatures,
            moments=moments,
            fiber_history=fiber_history,
            theta=theta,
            max_curvature=max_curvature,
            converged=converged,
        )
    
    def plot(
        self,
        axial_load: float = 0.0,
        number_of_points: int = 100,
        max_curvature: float = 0.004,
        number_of_iterations: int = 200,
        theta: float = 0.0,
        use_protocol: bool = False,
        protocol: Optional[TimeSeries] = None,
        ax: Optional[plt.Axes] = None,
        label: Optional[str] = None,
        **plot_kwargs
    ) -> Tuple[plt.Axes, MomentCurvatureResults]:
        """
        Run analysis and plot moment-curvature response.
        
        Parameters
        ----------
        axial_load : float, optional
            Applied axial load [N]. Default is 0.0.
        number_of_points : int, optional
            Number of analysis steps. Default is 100.
        max_curvature : float, optional
            Maximum curvature [1/mm]. Default is 0.004.
        number_of_iterations : int, optional
            Maximum iterations per step. Default is 200.
        theta : float, optional
            Section rotation [degrees]. Default is 0.0.
        use_protocol : bool, optional
            Use cyclic protocol. Default is False.
        protocol : TimeSeries, optional
            Custom loading protocol.
        ax : plt.Axes, optional
            Matplotlib axes. If None, creates new figure.
        label : str, optional
            Plot label. If None, auto-generated.
        **plot_kwargs
            Additional arguments for plotting.
        
        Returns
        -------
        ax : plt.Axes
            The matplotlib axes.
        result : MomentCurvatureResults
            The analysis result.
        """
        result = self.solve(
            axial_load=axial_load,
            number_of_points=number_of_points,
            max_curvature=max_curvature,
            number_of_iterations=number_of_iterations,
            theta=theta,
            use_protocol=use_protocol,
            protocol=protocol,
        )
        
        if ax is None:
            _, ax = plt.subplots(figsize=(8, 5))
        
        if label is None:
            label = f"P = {result.axial_load:.2e} N, θ = {result.theta}°"
        
        ax.plot(result.curvatures, result.moments, label=label, **plot_kwargs)
        ax.set_xlabel("Curvature [1/mm]")
        ax.set_ylabel("Moment [N·mm]")
        ax.set_title("Moment-Curvature Response")
        ax.grid(True, alpha=0.3)
        ax.legend()
        
        return ax, result
    
    def plot_fibers(
        self,
        axial_load: float = 0.0,
        number_of_points: int = 100,
        max_curvature: float = 0.004,
        number_of_iterations: int = 200,
        theta: float = 0.0,
        use_protocol: bool = False,
        protocol: Optional[TimeSeries] = None,
        step: int = -1,
        color_by: str = "strain",
        cmap: str = "viridis",
        scale_by_area: bool = False,
        area_scale: float = 3000.0,
        constant_size: float = 30.0,
        show_outline: bool = True,
        ax: Optional[plt.Axes] = None,
    ) -> Tuple[plt.Axes, MomentCurvatureResults]:
        """
        Plot fiber state at a specific analysis step.
        
        Parameters
        ----------
        axial_load : float, optional
            Applied axial load [N]. Default is 0.0.
        number_of_points : int, optional
            Number of analysis steps. Default is 100.
        max_curvature : float, optional
            Maximum curvature [1/mm]. Default is 0.004.
        number_of_iterations : int, optional
            Maximum iterations per step. Default is 200.
        theta : float, optional
            Section rotation [degrees]. Default is 0.0.
        use_protocol : bool, optional
            Use cyclic protocol. Default is False.
        protocol : TimeSeries, optional
            Custom loading protocol.
        step : int, optional
            Analysis step to visualize. Default is -1 (last step).
        color_by : str, optional
            Color fibers by: 'strain', 'stress', or 'material'. Default is 'strain'.
        cmap : str, optional
            Matplotlib colormap name. Default is 'viridis'.
        scale_by_area : bool, optional
            Scale marker size by fiber area. Default is False.
        area_scale : float, optional
            Scaling factor for areas. Default is 3000.0.
        constant_size : float, optional
            Marker size if not scaling by area. Default is 30.0.
        show_outline : bool, optional
            Show section outline. Default is True.
        ax : plt.Axes, optional
            Matplotlib axes. If None, creates new figure.
        
        Returns
        -------
        ax : plt.Axes
            The matplotlib axes.
        result : MomentCurvatureResults
            The analysis result.
        """
        result = self.solve(
            axial_load=axial_load,
            number_of_points=number_of_points,
            max_curvature=max_curvature,
            number_of_iterations=number_of_iterations,
            theta=theta,
            use_protocol=use_protocol,
            protocol=protocol,
        )
        
        if ax is None:
            _, ax = plt.subplots(figsize=(7, 6))
        
        # Get fiber state at step
        data = result.get_fiber_state(step)
        y, z = data[:, 0], data[:, 1]
        A = data[:, 2]
        σ, ε = data[:, 4], data[:, 5]
        
        # Determine coloring
        if color_by == "stress":
            c, lab = σ, "σ [MPa]"
        elif color_by == "strain":
            c, lab = ε, "ε"
        else:
            c, lab, cmap = data[:, 3], "Material", "tab10"
        
        # Marker size
        s = area_scale * A if scale_by_area else constant_size
        
        # Scatter plot
        sc = ax.scatter(y, z, c=c, s=s, cmap=cmap,
                       edgecolors="k", linewidths=0.25, zorder=3)
        cbar = plt.colorbar(sc, ax=ax, pad=0.01)
        cbar.set_label(lab)
        
        # Section outline
        if show_outline and hasattr(self.section, 'B') and hasattr(self.section, 'H'):
            B, H = self.section.B, self.section.H
            ax.add_patch(Rectangle(
                (-B/2, -H/2), B, H,
                facecolor='none', edgecolor='k',
                linestyle='--', linewidth=1.0
            ))
        
        # Axes settings
        ax.set_aspect('equal')
        ax.grid(True, alpha=0.3)
        ax.set_xlabel("y [mm]")
        ax.set_ylabel("z [mm]")
        ax.set_title(f"Fiber State – Step {step}\nκ = {result.curvatures[step]:.4e} [1/mm]")
        
        return ax, result