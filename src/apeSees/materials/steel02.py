from apeSees.materials.base import Material
from typing import Any, Optional

# Assuming apeSees.materials.base is available in the Python path
# (Content fetched from nmorabowen/apesees/apeSees-66420558d9652ba95ba906ae9714dfd264cf6608/src/apeSees/materials/base.py)

class Steel02(Material):
    """
    Represents the OpenSees Steel02 uniaxial material (Giuffré-Menegotto-Pinto).

    This class inherits from the base Material class and provides
    a specific interface for the Steel02 parameters.

    OpenSees Documentation Parameters:
    matTag, fy, E, b, R0, cR1, cR2, <a1, a2, a3, a4>
    
    Parameters
    ----------
    tag : int
        Unique material tag.
    fy : float
        Yield strength.
    e : float
        Young's modulus.
    b : float
        Strain hardening ratio (E_sh / E).
    r0 : float, optional
        Parameter controlling transition from elastic to plastic.
        (Default: 20.0, as used in examples)
    cr1 : float, optional
        Parameter controlling transition from elastic to plastic.
        (Default: 0.925, as used in examples)
    cr2 : float, optional
        Parameter controlling transition from elastic to plastic.
        (Default: 0.15, as used in examples)
    a1 : float, optional
        Isotropic hardening parameter (Default: 0.0)
    a2 : float, optional
        Isotropic hardening parameter (Default: 1.0)
    a3 : float, optional
        Isotropic hardening parameter (Default: 0.0)
    a4 : float, optional
        Isotropic hardening parameter (Default: 1.0)
    """
    def __init__(self,
                 tag: int,
                 fy: float,
                 e: float,
                 b: float,
                 r0: float = 20.0,
                 cr1: float = 0.925,
                 cr2: float = 0.15,
                 a1: Optional[float] = None,
                 a2: Optional[float] = None,
                 a3: Optional[float] = None,
                 a4: Optional[float] = None):
        
        # Collect all parameters in the exact positional order
        # required by OpenSees
        mat_params = [fy, e, b, r0, cr1, cr2]
        
        # Add optional isotropic hardening parameters if provided
        opt_params = [a1, a2, a3, a4]
        if any(p is not None for p in opt_params):
            # If any are specified, all must be (or OpenSees defaults)
            # We'll default them here if only some are given,
            # assuming user wants isotropic hardening.
            a1 = a1 if a1 is not None else 0.0
            a2 = a2 if a2 is not None else 1.0
            a3 = a3 if a3 is not None else 0.0
            a4 = a4 if a4 is not None else 1.0
            mat_params.extend([a1, a2, a3, a4])

        # Call the parent class __init__
        # It expects (mat_type, tag, *params)
        super().__init__("Steel02", tag, *mat_params)

