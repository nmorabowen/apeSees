"""Base classes and data structures for OpenSees time series."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Tuple

import matplotlib.pyplot as plt


@dataclass
class TimeSeriesData:
    """Data class for serializing time series information."""
    type: str
    tag: int
    time: list
    values: list
    parameters: dict


class TimeSeries(ABC):
    """Abstract base for all OpenSees time series."""

    @abstractmethod
    def build(self, verbose:bool = False) -> int:
        """
        Build the time series in OpenSees and return its tag.
        Verbose mode prints the OpenSees command used.
        
        Returns:
            int: The tag of the created time series.
        """
        pass

    @abstractmethod
    def plot(
        self,
        ax: Optional[plt.Axes] = None,
        figsize: Tuple[float, float] = (6, 4),
        **kwargs
    ) -> plt.Axes:
        """
        Plot the time series over the interval [0, 1].
        
        Args:
            ax: Matplotlib axes to plot on. If None, creates new figure.
            figsize: Figure size as (width, height) in inches.
            **kwargs: Additional arguments passed to ax.plot().
            
        Returns:
            plt.Axes: The axes object with the plot.
        """
        pass

    @abstractmethod
    def to_dataclass(self) -> TimeSeriesData:
        """
        Export time series data as a dataclass for serialization.
        
        Returns:
            TimeSeriesData: Dataclass containing all time series information.
        """
        pass