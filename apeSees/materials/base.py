"""Base material class for apeSees uniaxial materials."""

from __future__ import annotations
from typing import Any, Optional, Tuple

import matplotlib.pyplot as plt
import openseespy.opensees as ops

from .tester import UniaxialMaterialTester
from .results import MaterialTestResult


class Material:
    """
    Generic uniaxial material factory for OpenSees.

    Parameters
    ----------
    mat_type : str
        The OpenSees uniaxial material type (e.g., 'Steel02', 'Concrete02').
    tag : int
        Unique material tag.
    *params : Any
        Material parameters in the exact positional order required by OpenSees.

    Examples
    --------
    >>> steel = Material("Steel02", 1, 420.0, 200000.0, 0.01, 20.0, 0.925, 0.15)
    >>> tag = steel.build()
    >>> ax, result = steel.cyclic_tester(max_strain=0.02)
    >>> print(f"Peak stress: {result.peak_stress}")
    >>> plt.show()
    """

    def __init__(self, mat_type: str, tag: int, *params: Any):
        self.mat_type: str = str(mat_type)
        self.tag: int = int(tag)
        self.params: list[Any] = list(params)

        if not self.params:
            raise ValueError(
                f"No parameters provided for material '{self.mat_type}'. "
                f"Expected positional arguments in OpenSees order."
            )
        
        self.tester: UniaxialMaterialTester = UniaxialMaterialTester(material_object=self)

    def build(self, verbose: bool = False) -> int:
        """
        Define the material in OpenSees and return its tag.
        
        Parameters
        ----------
        verbose : bool, optional
            If True, prints the OpenSees command being executed. Default is False.
        
        Returns
        -------
        int
            The material tag.
            
        Examples
        --------
        >>> steel = Material("Steel02", 1, 420.0, 200000.0, 0.01, 20.0, 0.925, 0.15)
        >>> tag = steel.build(verbose=True)
        ops.uniaxialMaterial("Steel02", 1, 420.0, 200000.0, 0.01, 20.0, 0.925, 0.15)
        """
        ops.uniaxialMaterial(self.mat_type, self.tag, *self.params)
        
        if verbose:
            params_str = ", ".join(map(str, self.params))
            print(f'ops.uniaxialMaterial("{self.mat_type}", {self.tag}, {params_str})')
        
        return self.tag
    
    def cyclic_tester(
        self,
        *,
        max_strain: float,
        protocol_type: str = 'asce41',
        number_of_points: int = 1000,
        ax: Optional[plt.Axes] = None,
        figsize: Tuple[float, float] = (10, 6),
        show_backbone: bool = True,
        hysteresis_color: str = '#000077',
        backbone_color: str = 'black',
        **kwargs
    ) -> Tuple[plt.Axes, MaterialTestResult]:
        """
        Plot cyclic response with optional backbone overlay.
        
        Parameters
        ----------
        max_strain : float
            Maximum strain amplitude.
        protocol_type : str, optional
            Loading protocol: 'asce41', 'atc24', or 'fema461'. Default is 'asce41'.
        number_of_points : int, optional
            Number of analysis steps. Default is 1000.
        ax : plt.Axes, optional
            Matplotlib axes. If None, creates new figure.
        figsize : tuple, optional
            Figure size in inches. Default is (10, 6).
        show_backbone : bool, optional
            Whether to overlay backbone curve. Default is True.
        hysteresis_color : str, optional
            Color for hysteresis loops. Default is '#000077'.
        backbone_color : str, optional
            Color for backbone curve. Default is 'black'.
        **kwargs
            Additional arguments passed to the plot functions.
        
        Returns
        -------
        ax : plt.Axes
            The matplotlib axes with the plot.
        result : MaterialTestResult
            Test result containing strain, stress, and metadata.
        
        Examples
        --------
        >>> steel = Material("Steel02", 1, 420.0, 200000.0, 0.01, 20.0, 0.925, 0.15)
        >>> ax, result = steel.cyclic_tester(max_strain=0.02)
        >>> print(f"Peak stress: {result.peak_stress} MPa")
        >>> print(f"Energy dissipated: {result.energy_dissipated} J")
        >>> plt.show()
        
        >>> # Custom protocol
        >>> ax, result = steel.cyclic_tester(max_strain=0.03, protocol_type='fema461', show_backbone=False)
        >>> result.save('fema461_test.npz')
        >>> plt.show()
        """
        from ..timeseries import ASCE41Protocol, ModifiedATC24Protocol, FEMA461Protocol
        
        if ax is None:
            _, ax = plt.subplots(figsize=figsize)
        
        # Select protocol
        protocol_map = {
            'asce41': ASCE41Protocol,
            'atc24': ModifiedATC24Protocol,
            'fema461': FEMA461Protocol,
        }
        
        protocol_type_lower = protocol_type.lower()
        if protocol_type_lower not in protocol_map:
            raise ValueError(
                f"Unknown protocol_type '{protocol_type}'. "
                f"Choose from: {list(protocol_map.keys())}"
            )
        
        protocol_class = protocol_map[protocol_type_lower]
        protocol = protocol_class(tag=1, max_disp=max_strain)
        
        # Plot hysteresis and get result
        ax, result = self.tester.plot(
            time_series=protocol,
            number_of_points=number_of_points,
            ax=ax,
            label=f'Hysteretic Response - {self.name}',
            linestyle='-',
            color=hysteresis_color,
            linewidth=1.0,
            title='Uniaxial Hysteretic Response',
        )
        
        # Overlay backbone if requested
        if show_backbone:
            ax, backbone_result = self.tester.plot_backbone(
                strain_max=max_strain,
                strain_min=-max_strain,
                ax=ax,
                linestyle='--',
                color=backbone_color,
                linewidth=3,
                label='Backbone',
                title=None,  # Don't override title
            )
        
        ax.legend()
        
        return ax, results

    def backbone_tester(
        self,
        *,
        max_strain: float,
        number_of_points: int = 100,
        ax: Optional[plt.Axes] = None,
        figsize: Tuple[float, float] = (10, 6),
        **kwargs
    ) -> Tuple[plt.Axes, MaterialTestResult]:
        """
        Plot monotonic backbone curve.
        
        Parameters
        ----------
        max_strain : float
            Maximum strain amplitude (absolute value).
        number_of_points : int, optional
            Number of points per branch. Default is 100.
        ax : plt.Axes, optional
            Matplotlib axes. If None, creates new figure.
        figsize : tuple, optional
            Figure size in inches. Default is (10, 6).
        **kwargs
            Additional arguments passed to ax.plot().
        
        Returns
        -------
        ax : plt.Axes
            The matplotlib axes with the plot.
        result : MaterialTestResult
            Test result containing strain, stress, and metadata.
        
        Examples
        --------
        >>> steel = Material("Steel02", 1, 420.0, 200000.0, 0.01, 20.0, 0.925, 0.15)
        >>> ax, result = steel.backbone_tester(max_strain=0.03)
        >>> print(f"Peak stress: {result.peak_stress} MPa")
        >>> result.save('backbone_test.npz')
        >>> plt.show()
        """
        if ax is None:
            _, ax = plt.subplots(figsize=figsize)
        
        # Set defaults if not provided
        plot_kwargs = {
            'linestyle': '-',
            'color': 'black',
            'linewidth': 2,
            'label': f'Backbone - {self.name}'
        }
        plot_kwargs.update(kwargs)
        
        ax, result = self.tester.plot_backbone(
            strain_max=max_strain,
            strain_min=-max_strain,
            number_of_points=number_of_points,
            ax=ax,
            **plot_kwargs
        )
        
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        return ax, result
    
    @property
    def name(self) -> str:
        """
        Material name for display purposes.
        
        Returns
        -------
        str
            Formatted name with type and tag.
        """
        return f"{self.mat_type} - matTag:{self.tag}"
    
    def __repr__(self) -> str:
        return f"Material({self.mat_type!r}, tag={self.tag}, params={self.params})"