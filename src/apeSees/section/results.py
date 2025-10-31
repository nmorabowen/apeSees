"""Result data structures for section analysis."""

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional

import numpy as np
import matplotlib.pyplot as plt


@dataclass
class MomentCurvatureResults:
    """
    Results from a moment-curvature analysis.
    
    Attributes
    ----------
    axial_load : float
        Applied axial load [N].
    curvatures : np.ndarray
        Array of curvature values [1/mm].
    moments : np.ndarray
        Array of moment values [N·mm].
    fiber_history : np.ndarray
        Fiber state history with shape (n_steps, n_fibers, 6).
        Each fiber row contains: [y, z, area, mat_tag, stress, strain].
    theta : float, optional
        Rotation angle [degrees]. Default is 0.0.
    max_curvature : float, optional
        Maximum target curvature [1/mm].
    converged : bool
        Whether the analysis converged successfully. Default is True.
    
    Examples
    --------
    >>> result = MomentCurvatureResults(
    ...     axial_load=-1000000.0,
    ...     curvatures=curvature_array,
    ...     moments=moment_array,
    ...     fiber_history=fiber_data
    ... )
    >>> print(f"Peak moment: {result.peak_moment:.2e} N·mm")
    >>> result.plot()
    >>> plt.show()
    """
    
    axial_load: float
    curvatures: np.ndarray
    moments: np.ndarray
    fiber_history: np.ndarray
    theta: float = 0.0
    max_curvature: Optional[float] = None
    converged: bool = True
    
    def __post_init__(self):
        """Validate array shapes."""
        if len(self.curvatures) != len(self.moments):
            raise ValueError(
                f"Curvature and moment arrays must have same length: "
                f"{len(self.curvatures)} != {len(self.moments)}"
            )
        
        if self.fiber_history.ndim != 3 or self.fiber_history.shape[-1] != 6:
            raise ValueError(
                f"fiber_history must have shape (n_steps, n_fibers, 6), "
                f"got {self.fiber_history.shape}"
            )
    
    @property
    def peak_moment(self) -> float:
        """Maximum absolute moment value [N·mm]."""
        return float(np.max(np.abs(self.moments)))
    
    @property
    def peak_curvature(self) -> float:
        """Maximum absolute curvature value [1/mm]."""
        return float(np.max(np.abs(self.curvatures)))
    
    @property
    def num_steps(self) -> int:
        """Number of analysis steps."""
        return len(self.curvatures)
    
    @property
    def num_fibers(self) -> int:
        """Number of fibers in the section."""
        return self.fiber_history.shape[1]
    
    def plot(
        self,
        ax: Optional[plt.Axes] = None,
        figsize: tuple[float, float] = (8, 5),
        label: Optional[str] = None,
        **kwargs
    ) -> plt.Axes:
        """
        Plot moment-curvature response.
        
        Parameters
        ----------
        ax : plt.Axes, optional
            Matplotlib axes. If None, creates new figure.
        figsize : tuple, optional
            Figure size in inches. Default is (8, 5).
        label : str, optional
            Plot label. If None, auto-generated from axial load.
        **kwargs
            Additional arguments passed to ax.plot().
        
        Returns
        -------
        plt.Axes
            The matplotlib axes.
        """
        if ax is None:
            _, ax = plt.subplots(figsize=figsize)
        
        if label is None:
            label = f"P = {self.axial_load/1e6:.1f} MN"
        
        ax.plot(self.curvatures, self.moments, label=label, **kwargs)
        ax.set_xlabel("Curvature [1/mm]")
        ax.set_ylabel("Moment [N·mm]")
        ax.set_title("Moment-Curvature Response")
        ax.grid(True, alpha=0.3)
        ax.legend()
        
        return ax
    
    def get_fiber_state(self, step: int) -> np.ndarray:
        """
        Get fiber state at a specific step.
        
        Parameters
        ----------
        step : int
            Analysis step index.
        
        Returns
        -------
        np.ndarray
            Fiber data with shape (n_fibers, 6): [y, z, area, mat_tag, stress, strain].
        """
        if step < 0 or step >= self.num_steps:
            raise IndexError(f"Step {step} out of range [0, {self.num_steps-1}]")
        
        return self.fiber_history[step]
    
    def save(self, filepath: str) -> None:
        """
        Save results to a NumPy .npz file.
        
        Parameters
        ----------
        filepath : str
            Path to save file (e.g., 'mc_results.npz').
        """
        np.savez(
            filepath,
            axial_load=self.axial_load,
            curvatures=self.curvatures,
            moments=self.moments,
            fiber_history=self.fiber_history,
            theta=self.theta,
            max_curvature=self.max_curvature or 0.0,
            converged=self.converged,
        )
    
    @classmethod
    def load(cls, filepath: str) -> MomentCurvatureResults:
        """
        Load results from a NumPy .npz file.
        
        Parameters
        ----------
        filepath : str
            Path to .npz file.
        
        Returns
        -------
        MomentCurvatureResults
            Loaded analysis result.
        """
        data = np.load(filepath, allow_pickle=True)
        
        return cls(
            axial_load=float(data['axial_load']),
            curvatures=data['curvatures'],
            moments=data['moments'],
            fiber_history=data['fiber_history'],
            theta=float(data['theta']),
            max_curvature=float(data['max_curvature']) if data['max_curvature'] != 0.0 else None,
            converged=bool(data['converged']),
        )
    
    def __repr__(self) -> str:
        return (
            f"MomentCurvatureResults("
            f"P={self.axial_load/1e6:.2f} MN, "
            f"steps={self.num_steps}, "
            f"fibers={self.num_fibers}, "
            f"peak_M={self.peak_moment/1e9:.2f} GN·mm)"
        )