"""Uniaxial material testing utilities for apeSees."""

from typing import TYPE_CHECKING, Optional, Tuple

import numpy as np
import matplotlib.pyplot as plt
import openseespy.opensees as ops

from ..timeseries import TimeSeries, LinearTimeSeries
from .results import MaterialTestResult

if TYPE_CHECKING:
    from .base import Material


class UniaxialMaterialTester:
    """
    Test framework for uniaxial materials using OpenSees.
    
    This class provides low-level testing methods. For convenience,
    use the Material class methods like cyclic_tester() and backbone_tester().
    
    Examples
    --------
    >>> from apeSees.timeseries import ASCE41Protocol
    >>> 
    >>> tester = UniaxialMaterialTester(material)
    >>> protocol = ASCE41Protocol(tag=1, max_disp=0.02)
    >>> result = tester.run(protocol, number_of_points=500)
    >>> ax, result = tester.plot(protocol)
    """
    
    def __init__(self, material_object: "Material"):
        """
        Initialize the material tester.
        
        Parameters
        ----------
        material_object : Material
            Material instance with a `build()` method that returns an OpenSees material tag.
        """
        self.material_obj: "Material" = material_object

    def run(
        self,
        time_series: TimeSeries,
        number_of_points: int = 100,
    ) -> MaterialTestResult:
        """
        Run a static analysis with the given time series.
        
        Parameters
        ----------
        time_series : TimeSeries
            TimeSeries object defining the loading history.
        number_of_points : int, optional
            Number of analysis steps. Default is 100.
            
        Returns
        -------
        MaterialTestResult
            Test result containing strain, stress, and metadata.
            
        Examples
        --------
        >>> from apeSees.timeseries import ASCE41Protocol
        >>> protocol = ASCE41Protocol(tag=1, max_disp=0.02)
        >>> result = tester.run(protocol, number_of_points=500)
        >>> print(result.peak_stress)
        """
        ops.wipe()
        ops.model('basic', '-ndm', 1, '-ndf', 1)
        
        # Create nodes
        node_1 = 1
        ops.node(node_1, 0.0)
        ops.fix(node_1, 1)
        
        node_2 = 2
        ops.node(node_2, 1.0)
        
        # Create truss element with material
        mat_tag = self.material_obj.build()
        element_tag = 1
        area = 1.0
        ops.element('truss', element_tag, node_1, node_2, area, mat_tag)

        # Build time series and load pattern
        time_series_tag = time_series.build()
        load_pattern_tag = 1
        ops.pattern("Plain", load_pattern_tag, time_series_tag, '-fact', 1.0)
        ops.sp(node_2, 1, 1.0)

        # Set up analysis
        displacement_increment = 1.0 / number_of_points
        
        ops.system('UmfPack')
        ops.constraints('Transformation')
        ops.integrator('LoadControl', displacement_increment)
        ops.test('NormDispIncr', 1.0e-6, 10)
        ops.algorithm('Newton')
        ops.numberer('RCM')
        ops.analysis('Static')

        # Initialize result arrays
        stress_array = np.zeros(number_of_points + 1)
        strain_array = np.zeros(number_of_points + 1)
        time_array = np.linspace(0, 1, number_of_points + 1)

        # Record initial state
        ops.record()
        strain_array[0] = ops.nodeDisp(node_2, 1)
        stress_array[0] = ops.eleResponse(element_tag, 'axialForce')[0]
        
        # Run analysis
        converged = True
        for i in range(number_of_points):
            if ops.analyze(1) != 0:
                converged = False
                # Truncate arrays to successful steps
                strain_array = strain_array[:i+1]
                stress_array = stress_array[:i+1]
                time_array = time_array[:i+1]
                break
            
            strain_array[i + 1] = ops.nodeDisp(node_2, 1)
            stress_array[i + 1] = ops.eleResponse(element_tag, 'axialForce')[0]
            
        ops.wipe()
        
        # Get protocol name if available
        protocol_name = type(time_series).__name__
        
        return MaterialTestResult(
            strain=strain_array,
            stress=stress_array,
            time=time_array,
            converged=converged,
            material_tag=mat_tag,
            protocol_name=protocol_name,
        )

    def plot(
        self,
        time_series: TimeSeries,
        number_of_points: int = 500,
        ax: Optional[plt.Axes] = None,
        figsize: Tuple[float, float] = (10, 6),
        xlabel: str = 'Strain',
        ylabel: str = 'Stress',
        title: Optional[str] = None,
        **kwargs
    ) -> Tuple[plt.Axes, MaterialTestResult]:
        """
        Run analysis and plot the stress-strain response.
        
        Parameters
        ----------
        time_series : TimeSeries
            TimeSeries object defining loading history.
        number_of_points : int, optional
            Number of analysis steps. Default is 500.
        ax : plt.Axes, optional
            Matplotlib axes. If None, creates new figure.
        figsize : tuple, optional
            Figure size in inches. Default is (10, 6).
        xlabel : str, optional
            X-axis label. Default is 'Strain'.
        ylabel : str, optional
            Y-axis label. Default is 'Stress'.
        title : str, optional
            Plot title. If None, no title is set.
        **kwargs
            Additional arguments passed to ax.plot().
            
        Returns
        -------
        ax : plt.Axes
            The matplotlib axes.
        result : MaterialTestResult
            The test result data.
            
        Examples
        --------
        >>> from apeSees.timeseries import FEMA461Protocol
        >>> protocol = FEMA461Protocol(tag=1, max_disp=0.03)
        >>> ax, result = tester.plot(protocol, label='FEMA-461')
        >>> plt.show()
        """
        result = self.run(time_series, number_of_points=number_of_points)
        
        if ax is None:
            _, ax = plt.subplots(figsize=figsize)
        
        ax.plot(result.strain, result.stress, **kwargs)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        
        if title:
            ax.set_title(title)
        
        ax.grid(True, alpha=0.3)
        
        
        return ax, result

    def get_backbone(
        self,
        strain_max: float,
        strain_min: float,
        number_of_points: int = 100
    ) -> MaterialTestResult:
        """
        Get monotonic backbone curve (negative and positive branches).
        
        Parameters
        ----------
        strain_max : float
            Maximum positive strain.
        strain_min : float
            Minimum (negative) strain.
        number_of_points : int, optional
            Number of points per branch. Default is 100.
            
        Returns
        -------
        MaterialTestResult
            Backbone test result.
            
        Examples
        --------
        >>> result = tester.get_backbone(
        ...     strain_max=0.02, strain_min=-0.02, number_of_points=100
        ... )
        >>> print(f"Peak stress: {result.peak_stress}")
        """
        if strain_max <= 0:
            raise ValueError(f"strain_max must be positive, got {strain_max}")
        if strain_min >= 0:
            raise ValueError(f"strain_min must be negative, got {strain_min}")
        
        # Run positive branch
        ts_pos = LinearTimeSeries(tag=1, factor=strain_max)
        result_pos = self.run(time_series=ts_pos, number_of_points=number_of_points)

        # Run negative branch
        ts_neg = LinearTimeSeries(tag=1, factor=strain_min)
        result_neg = self.run(time_series=ts_neg, number_of_points=number_of_points)

        # Reverse negative branch
        strain_neg = result_neg.strain[::-1][:-1]
        stress_neg = result_neg.stress[::-1][:-1]

        # Concatenate
        strain_backbone = np.concatenate((strain_neg, result_pos.strain))
        stress_backbone = np.concatenate((stress_neg, result_pos.stress))
        time_backbone = np.linspace(0, 1, len(strain_backbone))

        return MaterialTestResult(
            strain=strain_backbone,
            stress=stress_backbone,
            time=time_backbone,
            converged=result_pos.converged and result_neg.converged,
            material_tag=result_pos.material_tag,
            protocol_name="Backbone",
        )
    
    def plot_backbone(
        self,
        strain_max: float,
        strain_min: float,
        number_of_points: int = 100,
        ax: Optional[plt.Axes] = None,
        figsize: Tuple[float, float] = (10, 6),
        xlabel: str = 'Strain',
        ylabel: str = 'Stress',
        title: Optional[str] = 'Monotonic Backbone Curve',
        **kwargs
    ) -> Tuple[plt.Axes, MaterialTestResult]:
        """
        Plot monotonic backbone curve.
        
        Parameters
        ----------
        strain_max : float
            Maximum positive strain.
        strain_min : float
            Minimum (negative) strain.
        number_of_points : int, optional
            Number of points per branch. Default is 100.
        ax : plt.Axes, optional
            Matplotlib axes. If None, creates new figure.
        figsize : tuple, optional
            Figure size in inches. Default is (10, 6).
        xlabel : str, optional
            X-axis label. Default is 'Strain'.
        ylabel : str, optional
            Y-axis label. Default is 'Stress'.
        title : str, optional
            Plot title. Default is 'Monotonic Backbone Curve'.
        **kwargs
            Additional arguments passed to ax.plot().
            
        Returns
        -------
        ax : plt.Axes
            The matplotlib axes.
        result : MaterialTestResult
            The test result data.
            
        Examples
        --------
        >>> ax, result = tester.plot_backbone(
        ...     strain_max=0.02, strain_min=-0.02, label='Backbone', color='blue'
        ... )
        >>> plt.show()
        """
        result = self.get_backbone(strain_max, strain_min, number_of_points)
        
        if ax is None:
            _, ax = plt.subplots(figsize=figsize)
        
        ax.plot(result.strain, result.stress, **kwargs)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        
        if title:
            ax.set_title(title)
        
        ax.grid(True, alpha=0.3)
        
        return ax, result
    
    def compare_protocols(
        self,
        protocols: list[Tuple[TimeSeries, str]],
        number_of_points: int = 500,
        figsize: Tuple[float, float] = (12, 8),
        xlabel: str = 'Strain',
        ylabel: str = 'Stress',
        title: str = 'Protocol Comparison',
        save_results: bool = False,
    ) -> Tuple[plt.Figure, dict[str, MaterialTestResult]]:
        """
        Compare multiple loading protocols on the same plot.
        
        Parameters
        ----------
        protocols : list of tuples
            List of (TimeSeries, label) tuples.
        number_of_points : int, optional
            Number of analysis steps per protocol. Default is 500.
        figsize : tuple, optional
            Figure size in inches. Default is (12, 8).
        xlabel : str, optional
            X-axis label. Default is 'Strain'.
        ylabel : str, optional
            Y-axis label. Default is 'Stress'.
        title : str, optional
            Plot title. Default is 'Protocol Comparison'.
        save_results : bool, optional
            If True, returns results dictionary. Default is False.
            
        Returns
        -------
        fig : plt.Figure
            The matplotlib figure.
        results : dict[str, MaterialTestResult]
            Dictionary mapping protocol labels to their results (if save_results=True).
            Empty dict if save_results=False.
            
        Examples
        --------
        >>> from apeSees.timeseries import ASCE41Protocol, FEMA461Protocol
        >>> protocols = [
        ...     (ASCE41Protocol(tag=1, max_disp=0.02), 'ASCE-41'),
        ...     (FEMA461Protocol(tag=2, max_disp=0.02), 'FEMA-461'),
        ... ]
        >>> fig, results = tester.compare_protocols(protocols, save_results=True)
        >>> plt.show()
        >>> 
        >>> # Access individual results
        >>> print(f"ASCE-41 peak: {results['ASCE-41'].peak_stress:.2f}")
        >>> print(f"FEMA-461 energy: {results['FEMA-461'].energy_dissipated:.2e}")
        """
        fig, ax = plt.subplots(figsize=figsize)
        results = {}
        
        for time_series, label in protocols:
            result = self.run(time_series, number_of_points=number_of_points)
            ax.plot(result.strain, result.stress, label=label, linewidth=2)
            
            if save_results:
                results[label] = result
        
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        ax.set_title(title)
        ax.grid(True, alpha=0.3)
        ax.legend()
        
        return fig, results if save_results else {}