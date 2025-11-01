from apeSees.materials.base import Material
from typing import Any, Optional

# Assuming apeSees.materials.base is available in the Python path
# (Content fetched from nmorabowen/apesees/apeSees-66420558d9652ba95ba906ae9714dfd264cf6608/src/apeSees/materials/base.py)

class Steel01(Material):
    """
    Represents the OpenSees Steel01 uniaxial material.

    This is a bilinear steel material with kinematic hardening
    and optional isotropic hardening.

    OpenSees Documentation Parameters:
    matTag, Fy, E0, b, <a1, a2, a3, a4>
    
    Parameters
    ----------
    tag : int
        Unique material tag.
    fy : float
        Yield strength.
    e : float
        Initial elastic tangent (Young's modulus).
    b : float
        Strain hardening ratio (E_sh / E).
    a1 : float, optional
        Isotropic hardening parameter (Default: None)
    a2 : float, optional
        Isotropic hardening parameter (Default: None)
    a3 : float, optional
        Isotropic hardening parameter (Default: None)
    a4 : float, optional
        Isotropic hardening parameter (Default: None)
    """
    def __init__(self,
                 tag: int,
                 fy: float,
                 e: float,
                 b: float,
                 a1: Optional[float] = None,
                 a2: Optional[float] = None,
                 a3: Optional[float] = None,
                 a4: Optional[float] = None):
        
        # Collect all parameters in the exact positional order
        # required by OpenSees
        mat_params = [fy, e, b]
        
        # Add optional isotropic hardening parameters if provided
        opt_params = [a1, a2, a3, a4]
        
        # If any optional parameters are provided, add them all
        # (assuming user intends to use isotropic hardening)
        if any(p is not None for p in opt_params):
            # OpenSees expects all 4 if any are provided.
            # We default them if not specified by the user.
            a1 = a1 if a1 is not None else 0.0
            a2 = a2 if a2 is not None else 1.0 # Default values may vary,
            a3 = a3 if a3 is not None else 0.0 # user should check OpenSees docs
            a4 = a4 if a4 is not None else 1.0 # if specifying some but not all.
            mat_params.extend([a1, a2, a3, a4])

        # Call the parent class __init__
        # It expects (mat_type, tag, *params)
        super().__init__("Steel01", tag, *mat_params)

