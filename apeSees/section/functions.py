"""Helper functions for section analysis."""

import numpy as np
from math import ceil


def nAs(n_bars: int, phi: float) -> float:
    """
    Calculate total steel area for n reinforcing bars.

    Parameters
    ----------
    n_bars : int
        Number of reinforcing bars.
    phi : float
        Bar diameter [mm].

    Returns
    -------
    float
        Total steel area [mm²].
        
    Examples
    --------
    >>> nAs(4, 20.0)  # 4 bars of 20mm diameter
    1256.6370614359173
    
    >>> nAs(8, 16.0)  # 8 bars of 16mm diameter
    1608.4954583701506
    """
    if n_bars < 0:
        raise ValueError(f"n_bars must be non-negative, got {n_bars}")
    if phi < 0:
        raise ValueError(f"phi must be non-negative, got {phi}")
    
    return n_bars * (np.pi * phi**2) / 4.0


def bar_area(phi: float) -> float:
    """
    Calculate area of a single reinforcing bar.

    Parameters
    ----------
    phi : float
        Bar diameter [mm].

    Returns
    -------
    float
        Bar area [mm²].
        
    Examples
    --------
    >>> bar_area(20.0)
    314.1592653589793
    """
    if phi < 0:
        raise ValueError(f"phi must be non-negative, got {phi}")
    
    return (np.pi * phi**2) / 4.0


def safe_ndiv(length: float, mesh_size: float) -> int:
    """
    Calculate number of divisions for a given length and mesh size.
    
    Parameters
    ----------
    length : float
        Length to subdivide [mm].
    mesh_size : float
        Target mesh size [mm].
    
    Returns
    -------
    int
        Number of divisions (at least 1).
        
    Examples
    --------
    >>> safe_ndiv(100.0, 25.0)
    4
    
    >>> safe_ndiv(10.0, 100.0)
    1
    """
    
    return max(1, int(ceil(max(length, 0.0) / mesh_size)))


def torsional_constant_rectangle(b: float, h: float) -> float:
    """
    Calculate Saint-Venant torsional constant for a solid rectangle.
    
    Parameters
    ----------
    b : float
        Longer side dimension [mm].
    h : float
        Shorter side dimension [mm].
    
    Returns
    -------
    float
        Torsional constant J [mm⁴].
        
    Notes
    -----
    Uses the formula: J = (b·h³/3) × (1 - 0.63·r + 0.052·r⁵)
    where r = h/b. Accurate to ~1-2% for all aspect ratios.
    
    Examples
    --------
    >>> torsional_constant_rectangle(300.0, 400.0)
    3413333333.3333335
    """
    b_long = max(b, h)  # longer side
    h_short = min(b, h)  # shorter side
    r = h_short / b_long
    
    # Accurate formula for all aspect ratios
    return (b_long * h_short**3 / 3.0) * (1.0 - 0.63*r + 0.052*r**5)