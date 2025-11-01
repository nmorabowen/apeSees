from apeSees.materials.base import Material
from typing import Optional

# Assuming apeSees.materials.base is available in the Python path
# (Content from nmorabowen/apesees/apeSees-66420558d9652ba95ba906ae9714dfd264cf6608/src/apeSees/materials/base.py)

class Hysteretic(Material):
    """
    Represents the OpenSees Hysteretic uniaxial material.

    This material model features pinching, damage, and degraded
    unloading stiffness. The backbone can be bilinear or trilinear.

    OpenSees Documentation Parameters:
    matTag, s1p, e1p, s2p, e2p, <s3p, e3p>, 
    s1n, e1n, s2n, e2n, <s3n, e3n>, 
    pinchX, pinchY, damage1, damage2, <beta>
    
    Parameters
    ----------
    tag : int
        Unique material tag.
    s1p : float
        Stress at first point of the positive envelope.
    e1p : float
        Strain at first point of the positive envelope.
    s2p : float
        Stress at second point of the positive envelope.
    e2p : float
        Strain at second point of the positive envelope.
    s1n : float
        Stress at first point of the negative envelope.
    e1n : float
        Strain at first point of the negative envelope.
    s2n : float
        Stress at second point of the negative envelope.
    e2n : float
        Strain at second point of the negative envelope.
    pinch_x : float
        Pinching factor for strain during reloading.
    pinch_y : float
        Pinching factor for stress during reloading.
    damage1 : float
        Damage parameter due to ductility.
    damage2 : float
        Damage parameter due to energy.
    s3p : float, optional
        Stress at third (optional) point of the positive envelope.
    e3p : float, optional
        Strain at third (optional) point of the positive envelope.
    s3n : float, optional
        Stress at third (optional) point of the negative envelope.
    e3n : float, optional
        Strain at third (optional) point of the negative envelope.
    beta : float, optional
        Power for degraded unloading stiffness (Default: 0.0, per docs).
    """
    def __init__(self,
                 tag: int,
                 s1p: float, e1p: float,
                 s2p: float, e2p: float,
                 s1n: float, e1n: float,
                 s2n: float, e2n: float,
                 pinch_x: float,
                 pinch_y: float,
                 damage1: float,
                 damage2: float,
                 s3p: Optional[float] = None,
                 e3p: Optional[float] = None,
                 s3n: Optional[float] = None,
                 e3n: Optional[float] = None,
                 beta: Optional[float] = None):
        
        # Start with mandatory positive envelope points
        mat_params = [s1p, e1p, s2p, e2p]

        # Add optional positive point 3
        # Both s3p and e3p must be provided if one is.
        if (s3p is not None) and (e3p is not None):
            mat_params.extend([s3p, e3p])
        elif (s3p is not None) or (e3p is not None):
            raise ValueError("Both 's3p' and 'e3p' must be provided together, or both omitted.")

        # Add mandatory negative envelope points
        mat_params.extend([s1n, e1n, s2n, e2n])

        # Add optional negative point 3
        if (s3n is not None) and (e3n is not None):
            mat_params.extend([s3n, e3n])
        elif (s3n is not None) or (e3n is not None):
            raise ValueError("Both 's3n' and 'e3n' must be provided together, or both omitted.")

        # Add pinching, damage, and optional beta
        mat_params.extend([pinch_x, pinch_y, damage1, damage2])
        
        if beta is not None:
            mat_params.append(beta)

        # Call the parent class __init__
        # It expects (mat_type, tag, *params)
        super().__init__("Hysteretic", tag, *mat_params)

