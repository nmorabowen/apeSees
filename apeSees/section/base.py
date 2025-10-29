"""Base classes for structural sections."""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import matplotlib.pyplot as plt


class Section(ABC):
    """
    Abstract base class for all structural sections.
    
    All section types must implement:
    - build(): Define the section in OpenSees
    - plot_section(): Visualize the section geometry
    """
    
    @abstractmethod
    def build(self) -> int:
        """
        Build the section in OpenSees.
        
        Returns
        -------
        int
            The section tag.
        """
        pass
    
    @abstractmethod
    def plot_section(self, ax: plt.Axes | None = None, **kwargs) -> plt.Axes:
        """
        Plot the section geometry.
        
        Parameters
        ----------
        ax : plt.Axes, optional
            Matplotlib axes. If None, creates new figure.
        **kwargs
            Additional plotting arguments.
        
        Returns
        -------
        plt.Axes
            The matplotlib axes.
        """
        pass