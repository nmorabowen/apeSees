"""Result data structures for material testing."""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional

import numpy as np
import matplotlib.pyplot as plt


@dataclass
class MaterialTestResult:
    """
    Results from a uniaxial material test analysis.
    
    Attributes
    ----------
    strain : np.ndarray
        Array of strain values.
    stress : np.ndarray
        Array of stress values.
    time : np.ndarray
        Normalized analysis time (0 to 1).
    converged : bool
        Whether the analysis converged successfully.
    material_tag : int, optional
        OpenSees material tag used in the test.
    protocol_name : str, optional
        Name of the loading protocol used.
    metadata : dict, optional
        Additional metadata about the test.
    
    Examples
    --------
    >>> result = MaterialTestResult(strain=strain_arr, stress=stress_arr, time=time_arr, converged=True)
    >>> print(f"Peak stress: {result.peak_stress}")
    >>> result.plot()
    >>> result.save('test_results.npz')
    """
    
    strain: np.ndarray
    stress: np.ndarray
    time: np.ndarray
    converged: bool
    material_tag: int = 0
    protocol_name: Optional[str] = None
    metadata: dict = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate arrays have consistent shapes."""
        if not (len(self.strain) == len(self.stress) == len(self.time)):
            raise ValueError(
                f"Inconsistent array lengths: strain={len(self.strain)}, "
                f"stress={len(self.stress)}, time={len(self.time)}"
            )
    
    def plot(
        self,
        ax: Optional[plt.Axes] = None,
        figsize: tuple[float, float] = (10, 6),
        xlabel: str = 'Strain',
        ylabel: str = 'Stress',
        title: Optional[str] = None,
        **kwargs
    ) -> plt.Axes:
        """
        Plot the stress-strain response.
        
        Parameters
        ----------
        ax : plt.Axes, optional
            Matplotlib axes. If None, creates new figure.
        figsize : tuple, optional
            Figure size in inches.
        xlabel : str, optional
            X-axis label.
        ylabel : str, optional
            Y-axis label.
        title : str, optional
            Plot title. If None, auto-generated.
        **kwargs
            Additional arguments passed to ax.plot().
        
        Returns
        -------
        plt.Axes
            The matplotlib axes.
        """
        if ax is None:
            _, ax = plt.subplots(figsize=figsize)
        
        ax.plot(self.strain, self.stress, **kwargs)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        
        if title is None and self.protocol_name:
            title = f'Material Test - {self.protocol_name}'
        
        if title:
            ax.set_title(title)
        
        ax.grid(True, alpha=0.3)
        
        return ax
    
    def to_dict(self) -> dict:
        """
        Export results to dictionary.
        
        Returns
        -------
        dict
            Dictionary with all result data.
        """
        return {
            'strain': self.strain.tolist(),
            'stress': self.stress.tolist(),
            'time': self.time.tolist(),
            'converged': self.converged,
            'material_tag': self.material_tag,
            'protocol_name': self.protocol_name,
            'metadata': self.metadata,
        }
    
    def save(self, filepath: str) -> None:
        """
        Save results to a NumPy .npz file.
        
        Parameters
        ----------
        filepath : str
            Path to save file (e.g., 'results.npz').
        """
        np.savez(
            filepath,
            strain=self.strain,
            stress=self.stress,
            time=self.time,
            converged=self.converged,
            material_tag=self.material_tag,
            protocol_name=self.protocol_name or '',
        )
    
    @classmethod
    def load(cls, filepath: str) -> MaterialTestResult:
        """
        Load results from a NumPy .npz file.
        
        Parameters
        ----------
        filepath : str
            Path to .npz file.
        
        Returns
        -------
        MaterialTestResult
            Loaded test result.
        """
        data = np.load(filepath, allow_pickle=True)
        protocol_name = str(data['protocol_name']) if data['protocol_name'] else None
        
        return cls(
            strain=data['strain'],
            stress=data['stress'],
            time=data['time'],
            converged=bool(data['converged']),
            material_tag=int(data['material_tag']),
            protocol_name=protocol_name,
        )
    
    @property
    def peak_stress(self) -> float:
        """Maximum absolute stress value."""
        return float(np.max(np.abs(self.stress)))
    
    @property
    def peak_strain(self) -> float:
        """Maximum absolute strain value."""
        return float(np.max(np.abs(self.strain)))
    
    @property
    def energy_dissipated(self) -> float:
        """
        Approximate energy dissipated (area enclosed by hysteresis loop).
        
        For cyclic loading, this represents the total dissipated energy.
        For monotonic loading, this is the area under the curve.
        """
        return float(np.trapz(self.stress, self.strain))
    
    @property
    def num_points(self) -> int:
        """Number of data points in the result."""
        return len(self.strain)
    
    def __repr__(self) -> str:
        return (
            f"MaterialTestResult("
            f"points={self.num_points}, "
            f"converged={self.converged}, "
            f"peak_stress={self.peak_stress:.2f}, "
            f"energy={self.energy_dissipated:.2e})"
        )