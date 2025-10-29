"""Basic OpenSees time series: Linear, Constant, and Path."""

from typing import Optional, Tuple

import numpy as np
import matplotlib.pyplot as plt
import openseespy.opensees as ops

from .base import TimeSeries, TimeSeriesData


class LinearTimeSeries(TimeSeries):
    """
    Linear time series: value(t) = factor * t
    
    Examples:
        >>> ts = LinearTimeSeries(tag=1, factor=2.5)
        >>> ts.build()
        1
        >>> ts.plot()
    """

    def __init__(self, tag: int, factor: float = 1.0):
        self.tag: int = int(tag)
        self.factor: float = float(factor)

    def __repr__(self) -> str:
        return f"LinearTimeSeries(tag={self.tag}, factor={self.factor})"

    def build(self, verbose:bool = False) -> int:
        """
        Build the linear time series in OpenSees.
        
        Returns:
            int: The tag of the created time series.
        """
        ops.timeSeries("Linear", self.tag, "-factor", self.factor)
        
        if verbose:
            print(f'ops.timeSeries("Linear", {self.tag}, "-factor", {self.factor})')
        
        return self.tag

    def plot(
        self, 
        ax: Optional[plt.Axes] = None, 
        figsize: Tuple[float, float] = (6, 4),
        label: Optional[str] = None,
        **kwargs
    ) -> plt.Axes:
        """
        Plot the linear time series.
        
        Args:
            ax: Matplotlib axes to plot on. If None, creates new figure.
            figsize: Figure size as (width, height) in inches.
            label: Plot label for legend. If None, auto-generated.
            **kwargs: Additional arguments passed to ax.plot().
            
        Returns:
            plt.Axes: The axes object with the plot.
        """
        if ax is None:
            _, ax = plt.subplots(figsize=figsize)
        
        if label is None:
            label = f"Linear (factor={self.factor})"
        
        t = np.array([0.0, 1.0])
        value = np.array([0.0, self.factor])
        ax.plot(t, value, label=label, **kwargs)
        ax.set_xlabel("Time")
        ax.set_ylabel("Value")
        ax.legend()
        return ax

    def to_dataclass(self) -> TimeSeriesData:
        """
        Export linear time series data as a dataclass.
        
        Returns:
            TimeSeriesData: Dataclass containing time series information.
        """
        t = [0.0, 1.0]
        values = [0.0, self.factor]
        return TimeSeriesData(
            type="LinearTimeSeries",
            tag=self.tag,
            time=t,
            values=values,
            parameters={"factor": self.factor}
        )


class ConstantTimeSeries(TimeSeries):
    """
    Constant time series: value(t) = factor
    
    Examples:
        >>> ts = ConstantTimeSeries(tag=2, factor=5.0)
        >>> ts.build()
        2
        >>> ts.plot()
    """

    def __init__(self, tag: int, factor: float = 1.0):
        self.tag: int = int(tag)
        self.factor: float = float(factor)

    def __repr__(self) -> str:
        return f"ConstantTimeSeries(tag={self.tag}, factor={self.factor})"

    def build(self, verbose:bool = False) -> int:
        """
        Build the constant time series in OpenSees.
        
        Returns:
            int: The tag of the created time series.
        """
        ops.timeSeries("Constant", self.tag, "-factor", self.factor)
        
        if verbose:
            print(f'ops.timeSeries("Constant", {self.tag}, "-factor", {self.factor})')
        
        return self.tag

    def plot(
        self, 
        ax: Optional[plt.Axes] = None, 
        figsize: Tuple[float, float] = (6, 4),
        label: Optional[str] = None,
        **kwargs
    ) -> plt.Axes:
        """
        Plot the constant time series.
        
        Args:
            ax: Matplotlib axes to plot on. If None, creates new figure.
            figsize: Figure size as (width, height) in inches.
            label: Plot label for legend. If None, auto-generated.
            **kwargs: Additional arguments passed to ax.plot().
            
        Returns:
            plt.Axes: The axes object with the plot.
        """
        if ax is None:
            _, ax = plt.subplots(figsize=figsize)
        
        if label is None:
            label = f"Constant (factor={self.factor})"
        
        t = np.array([0.0, 1.0])
        value = np.array([self.factor, self.factor])
        ax.plot(t, value, label=label, **kwargs)
        ax.set_xlabel("Time")
        ax.set_ylabel("Value")
        ax.legend()
        return ax

    def to_dataclass(self) -> TimeSeriesData:
        """
        Export constant time series data as a dataclass.
        
        Returns:
            TimeSeriesData: Dataclass containing time series information.
        """
        t = [0.0, 1.0]
        values = [self.factor, self.factor]
        return TimeSeriesData(
            type="ConstantTimeSeries",
            tag=self.tag,
            time=t,
            values=values,
            parameters={"factor": self.factor}
        )


class PathTimeSeries(TimeSeries):
    """
    Path time series: explicit time–value pairs.
    
    Examples:
        >>> time = np.array([0.0, 1.0, 2.0])
        >>> values = np.array([0.0, 1.0, 0.0])
        >>> ts = PathTimeSeries(tag=3, time=time, values=values)
        >>> ts.build()
        3
        >>> ts.plot()
    """

    def __init__(
        self,
        tag: int,
        time: np.ndarray,
        values: np.ndarray,
        factor: float = 1.0,
        start_time: float = 0.0,
        use_last: bool = False,
        prepend_zero: bool = False,
    ):
        self.tag: int = int(tag)
        self.time: np.ndarray = np.asarray(time, dtype=float)
        self.values: np.ndarray = np.asarray(values, dtype=float)
        self.factor: float = float(factor)
        self.start_time: float = float(start_time)
        self.use_last: bool = bool(use_last)
        self.prepend_zero: bool = bool(prepend_zero)

        if self.time.shape != self.values.shape:
            raise ValueError("`time` and `values` must have the same shape")

    def __repr__(self) -> str:
        return f"PathTimeSeries(tag={self.tag}, n_points={len(self.time)}, factor={self.factor})"

    def build(self, verbose:bool = False) -> int:
        """
        Build the path time series in OpenSees.
        
        Returns:
            int: The tag of the created time series.
        """
        t = self.time
        v = self.values

        if self.prepend_zero and (t[0] != 0.0):
            t = np.concatenate([[0.0], t])
            v = np.concatenate([[0.0], v])

        args = ["-time", *t, "-values", *v, "-factor", self.factor, "-startTime", self.start_time]
        if self.use_last:
            args.append("-useLast")

        ops.timeSeries("Path", self.tag, *args)
        
        if verbose:
            print(f'ops.timeSeries("Path", {self.tag}, ' + ', '.join(f'"{arg}"' if isinstance(arg, str) else str(arg) for arg in args) + ')')
        
        return self.tag

    def plot(
        self, 
        ax: Optional[plt.Axes] = None, 
        figsize: Tuple[float, float] = (6, 4),
        label: Optional[str] = None,
        **kwargs
    ) -> plt.Axes:
        """
        Plot the path time series.
        
        Args:
            ax: Matplotlib axes to plot on. If None, creates new figure.
            figsize: Figure size as (width, height) in inches.
            label: Plot label for legend. If None, auto-generated.
            **kwargs: Additional arguments passed to ax.plot().
            
        Returns:
            plt.Axes: The axes object with the plot.
        """
        if ax is None:
            _, ax = plt.subplots(figsize=figsize)
        
        if label is None:
            label = f"Path (factor={self.factor})"
        
        t = self.time
        value = self.values * self.factor
        ax.plot(t, value, label=label, **kwargs)
        ax.set_xlabel("Time")
        ax.set_ylabel("Value")
        ax.legend()
        return ax

    def to_dataclass(self) -> TimeSeriesData:
        """
        Export path time series data as a dataclass.
        
        Returns:
            TimeSeriesData: Dataclass containing time series information.
        """
        return TimeSeriesData(
            type="PathTimeSeries",
            tag=self.tag,
            time=self.time.tolist(),
            values=self.values.tolist(),
            parameters={
                "factor": self.factor,
                "start_time": self.start_time,
                "use_last": self.use_last,
                "prepend_zero": self.prepend_zero
            }
        )