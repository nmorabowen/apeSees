"""Cyclic loading protocols: ASCE-41, Modified ATC-24, and FEMA-461."""

from typing import Optional, Tuple

import numpy as np
import matplotlib.pyplot as plt
import openseespy.opensees as ops

from .base import TimeSeries, TimeSeriesData


class ASCE41Protocol(TimeSeries):
    """
    ASCE-41 cyclic protocol with constant slope and unit time.
    
    The protocol follows ASCE 41-17 displacement-controlled testing with
    increasing amplitudes and decreasing repetitions.
    
    Examples:
        >>> ts = ASCE41Protocol(tag=10, max_disp=0.02)
        >>> ts.build()
        10
        >>> fig, ax = plt.subplots()
        >>> ts.plot(ax=ax)
        >>> plt.show()
    
    Args:
        tag: Unique identifier for the OpenSees time series.
        max_disp: Maximum displacement or strain value.
    """

    def __init__(self, tag: int, max_disp: float = 1.00):
        if max_disp <= 0:
            raise ValueError(f"max_disp must be positive, got {max_disp}")
        
        self.tag: int = int(tag)
        self.max_disp: float = float(max_disp)

        unit = np.array([0.0025, 0.005, 0.0075, 0.010, 0.015, 0.020, 0.030, 0.040, 0.060], dtype=float)
        unit /= unit.max()
        reps = np.array([3, 3, 3, 3, 3, 3, 2, 2, 2], dtype=int)

        vals = [0.0]
        for a, n in zip(unit, reps):
            A = float(a) * self.max_disp
            for _ in range(int(n)):
                vals += [+A, -A]
        vals += [0.0]
        self.disp: np.ndarray = np.asarray(vals, dtype=float)

        dv = np.abs(np.diff(self.disp))
        t = np.concatenate(([0.0], np.cumsum(dv)))
        t_max = t[-1]
        self.time: np.ndarray = t / t_max if t_max > 1e-10 else t

    def __repr__(self) -> str:
        return f"ASCE41Protocol(tag={self.tag}, max_disp={self.max_disp})"

    def build(self, verbose:bool = False) -> int:
        """
        Build the ASCE-41 protocol time series in OpenSees.
        
        Returns:
            int: The tag of the created time series.
        """
        ops.timeSeries("Path", self.tag, "-time", *self.time, "-values", *self.disp, "-factor", 1.0)
        
        if verbose:
            print(f'ops.timeSeries("Path", {self.tag}, "-time", ' + ', '.join(str(t) for t in self.time) + ', "-values", ' + ', '.join(str(v) for v in self.disp) + ', "-factor", 1.0)')
        
        return self.tag

    def plot(
        self, 
        ax: Optional[plt.Axes] = None, 
        figsize: Tuple[float, float] = (6, 4),
        label: Optional[str] = None,
        **kw
    ) -> plt.Axes:
        """
        Plot the ASCE-41 protocol.
        
        Args:
            ax: Matplotlib axes to plot on. If None, creates new figure.
            figsize: Figure size as (width, height) in inches.
            label: Plot label for legend. If None, auto-generated.
            **kw: Additional arguments passed to ax.plot().
            
        Returns:
            plt.Axes: The axes object with the plot.
        """
        if ax is None:
            _, ax = plt.subplots(figsize=figsize)
        
        if label is None:
            label = f"ASCE-41 (max={self.max_disp})"
        
        ax.plot(self.time, self.disp, label=label, **kw)
        ax.set_xlabel("Normalized time")
        ax.set_ylabel("Disp / Strain")
        ax.grid(True, ls="--", alpha=0.4)
        ax.legend()
        return ax

    def to_dataclass(self) -> TimeSeriesData:
        """
        Export ASCE-41 protocol data as a dataclass.
        
        Returns:
            TimeSeriesData: Dataclass containing time series information.
        """
        return TimeSeriesData(
            type="ASCE41Protocol",
            tag=self.tag,
            time=self.time.tolist(),
            values=self.disp.tolist(),
            parameters={"max_disp": self.max_disp}
        )


class ModifiedATC24Protocol(TimeSeries):
    """
    Modified ATC-24 cyclic protocol with constant slope and unit time.
    
    Examples:
        >>> ts = ModifiedATC24Protocol(tag=21, max_disp=0.03)
        >>> ts.build()
        21
        >>> ts.plot()
    """

    def __init__(self, tag: int, max_disp: float = 1.00):
        if max_disp <= 0:
            raise ValueError(f"max_disp must be positive, got {max_disp}")
        
        self.tag: int = int(tag)
        self.max_disp: float = float(max_disp)

        levels = np.array([0.1, 0.2, 0.3, 0.5, 0.7, 1.0], dtype=float)
        reps = np.array([3, 3, 3, 2, 2, 1], dtype=int)

        vals = [0.0]
        for a, n in zip(levels, reps):
            A = float(a) * self.max_disp
            for _ in range(int(n)):
                vals += [+A, -A]
        vals += [0.0]
        self.disp: np.ndarray = np.asarray(vals, dtype=float)

        dv = np.abs(np.diff(self.disp))
        t = np.concatenate(([0.0], np.cumsum(dv)))
        t_max = t[-1]
        self.time: np.ndarray = t / t_max if t_max > 1e-10 else t

    def __repr__(self) -> str:
        return f"ModifiedATC24Protocol(tag={self.tag}, max_disp={self.max_disp})"

    def build(self, verbose:bool = False) -> int:
        """
        Build the Modified ATC-24 protocol time series in OpenSees.
        
        Returns:
            int: The tag of the created time series.
        """
        ops.timeSeries("Path", self.tag, "-time", *self.time, "-values", *self.disp, "-factor", 1.0)
        
        if verbose:
            print(f'ops.timeSeries("Path", {self.tag}, "-time", ' + ', '.join(str(t) for t in self.time) + ', "-values", ' + ', '.join(str(v) for v in self.disp) + ', "-factor", 1.0)')
        
        return self.tag

    def plot(
        self, 
        ax: Optional[plt.Axes] = None, 
        figsize: Tuple[float, float] = (6, 4),
        label: Optional[str] = None,
        **kw
    ) -> plt.Axes:
        """
        Plot the Modified ATC-24 protocol.
        
        Args:
            ax: Matplotlib axes to plot on. If None, creates new figure.
            figsize: Figure size as (width, height) in inches.
            label: Plot label for legend. If None, auto-generated.
            **kw: Additional arguments passed to ax.plot().
            
        Returns:
            plt.Axes: The axes object with the plot.
        """
        if ax is None:
            _, ax = plt.subplots(figsize=figsize)
        
        if label is None:
            label = f"Modified ATC-24 (max={self.max_disp})"
        
        ax.plot(self.time, self.disp, label=label, **kw)
        ax.set_xlabel("Normalized time")
        ax.set_ylabel("Disp / Strain")
        ax.grid(True, ls="--", alpha=0.4)
        ax.legend()
        return ax

    def to_dataclass(self) -> TimeSeriesData:
        """
        Export Modified ATC-24 protocol data as a dataclass.
        
        Returns:
            TimeSeriesData: Dataclass containing time series information.
        """
        return TimeSeriesData(
            type="ModifiedATC24Protocol",
            tag=self.tag,
            time=self.time.tolist(),
            values=self.disp.tolist(),
            parameters={"max_disp": self.max_disp}
        )


class FEMA461Protocol(TimeSeries):
    """
    FEMA-461 cyclic protocol with constant slope and unit time.
    
    Examples:
        >>> ts = FEMA461Protocol(tag=31, max_disp=0.03, alpha=0.62)
        >>> ts.build()
        31
        >>> ts.plot()
    """

    def __init__(self, tag: int, max_disp: float = 1.00, alpha: float = 0.62):
        if max_disp <= 0:
            raise ValueError(f"max_disp must be positive, got {max_disp}")
        if alpha <= 0:
            raise ValueError(f"alpha must be positive, got {alpha}")
        
        self.tag: int = int(tag)
        self.max_disp: float = float(max_disp)
        self.alpha: float = float(alpha)

        vals = [0.0]
        d = 0.01 * self.max_disp  # start at 1% of max
        while abs(d) < self.max_disp:
            vals += [d, -d]
            d *= (1.0 + self.alpha)
        vals += [0.0]
        self.disp: np.ndarray = np.asarray(vals, dtype=float)

        dv = np.abs(np.diff(self.disp))
        t = np.concatenate(([0.0], np.cumsum(dv)))
        t_max = t[-1]
        self.time: np.ndarray = t / t_max if t_max > 1e-10 else t

    def __repr__(self) -> str:
        return f"FEMA461Protocol(tag={self.tag}, max_disp={self.max_disp}, alpha={self.alpha})"

    def build(self, verbose:bool = False) -> int:
        """
        Build the FEMA-461 protocol time series in OpenSees.
        
        Returns:
            int: The tag of the created time series.
        """
        ops.timeSeries("Path", self.tag, "-time", *self.time, "-values", *self.disp, "-factor", 1.0)
        
        if verbose:
            print(f'ops.timeSeries("Path", {self.tag}, "-time", ' + ', '.join(str(t) for t in self.time) + ', "-values", ' + ', '.join(str(v) for v in self.disp) + ', "-factor", 1.0)')
        
        return self.tag

    def plot(
        self, 
        ax: Optional[plt.Axes] = None, 
        figsize: Tuple[float, float] = (6, 4),
        label: Optional[str] = None,
        **kw
    ) -> plt.Axes:
        """
        Plot the FEMA-461 protocol.
        
        Args:
            ax: Matplotlib axes to plot on. If None, creates new figure.
            figsize: Figure size as (width, height) in inches.
            label: Plot label for legend. If None, auto-generated.
            **kw: Additional arguments passed to ax.plot().
            
        Returns:
            plt.Axes: The axes object with the plot.
        """
        if ax is None:
            _, ax = plt.subplots(figsize=figsize)
        
        if label is None:
            label = f"FEMA-461 (max={self.max_disp}, α={self.alpha})"
        
        ax.plot(self.time, self.disp, label=label, **kw)
        ax.set_xlabel("Normalized time")
        ax.set_ylabel("Disp / Strain")
        ax.grid(True, ls="--", alpha=0.4)
        ax.legend()
        return ax

    def to_dataclass(self) -> TimeSeriesData:
        """
        Export FEMA-461 protocol data as a dataclass.
        
        Returns:
            TimeSeriesData: Dataclass containing time series information.
        """
        return TimeSeriesData(
            type="FEMA461Protocol",
            tag=self.tag,
            time=self.time.tolist(),
            values=self.disp.tolist(),
            parameters={
                "max_disp": self.max_disp,
                "alpha": self.alpha
            }
        )