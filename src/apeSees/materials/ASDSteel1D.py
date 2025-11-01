from apeSees.materials.base import Material
from typing import Optional, Tuple

# Assuming apeSees.materials.base is available in the Python path
# (Content from nmorabowen/apesees/apeSees-66420558d9652ba95ba906ae9714dfd264cf6608/src/apeSees/materials/base.py)

class ASDSteel1D(Material):
    """
    Represents the OpenSees ASDSteel1D uniaxial material.

    This is a uniaxial material model for the nonlinear response of 
    reinforcing steel bars, integrating plasticity, damage, buckling,
    and bond-slip.

    OpenSees Documentation Parameters:
    uniaxialMaterial ASDSteel1D $tag $E $sy $su $eu
                             <-implex>
                             <-auto_regularization>
                             <-buckling $lch <$r>>
                             <-fracture <$r>>
                             <-slip $matTag <$r>>
                             <-K_alpha $K_alpha>
                             <-max_iter $max_iter>
                             <-tolU $tolU>
                             <-tolR $tolR>
    
    Parameters
    ----------
    tag : int
        Unique material tag.
    e : float
        Young's modulus.
    sy : float
        Yield stress.
    su : float
        Ultimate stress.
    eu : float
        Ultimate strain.
    implex : bool, optional
        If True, activates the IMPL-EX integration scheme. (Default: False)
    auto_regularization : bool, optional
        If True, activates automatic regularization. (Default: False)
    buckling : Tuple[float, Optional[float]], optional
        Enables buckling. Pass a tuple: (lch, r).
        lch: characteristic length
        r: section radius (optional)
        (Default: None)
    fracture : float, optional
        Activates fracture modeling. Pass the section radius 'r'.
        (Default: None)
    slip : Tuple[int, Optional[float]], optional
        Activates slip modeling. Pass a tuple: (matTag, r).
        matTag: tag of a secondary uniaxial material
        r: section radius (optional)
        (Default: None)
    k_alpha : float, optional
        Weight for consistent tangent modulus (Default: None, uses OpenSees default)
    max_iter : int, optional
        Max iterations for RVE loop (Default: None, uses OpenSees default)
    tol_u : float, optional
        Tolerance on displacement increment (Default: None, uses OpenSees default)
    tol_r : float, optional
        Tolerance on residual force (Default: None, uses OpenSees default)
    """
    def __init__(self,
                 tag: int,
                 e: float,
                 sy: float,
                 su: float,
                 eu: float,
                 implex: bool = False,
                 auto_regularization: bool = False,
                 buckling: Optional[Tuple[float, Optional[float]]] = None,
                 fracture: Optional[float] = None,
                 slip: Optional[Tuple[int, Optional[float]]] = None,
                 k_alpha: Optional[float] = None,
                 max_iter: Optional[int] = None,
                 tol_u: Optional[float] = None,
                 tol_r: Optional[float] = None):
        
        # Start with mandatory positional parameters
        mat_params = [e, sy, su, eu]
        
        # Add optional keyword parameters
        if implex:
            mat_params.append("-implex")
            
        if auto_regularization:
            mat_params.append("-auto_regularization")

        if buckling is not None:
            mat_params.append("-buckling")
            mat_params.append(buckling[0])  # lch
            if len(buckling) > 1 and buckling[1] is not None:
                mat_params.append(buckling[1]) # r

        if fracture is not None:
            mat_params.append("-fracture")
            mat_params.append(fracture) # r

        if slip is not None:
            mat_params.append("-slip")
            mat_params.append(slip[0]) # matTag
            if len(slip) > 1 and slip[1] is not None:
                mat_params.append(slip[1]) # r

        if k_alpha is not None:
            mat_params.extend(["-K_alpha", k_alpha])
            
        if max_iter is not None:
            mat_params.extend(["-max_iter", max_iter])

        if tol_u is not None:
            mat_params.extend(["-tolU", tol_u])

        if tol_r is not None:
            mat_params.extend(["-tolR", tol_r])

        # Call the parent class __init__
        # It expects (mat_type, tag, *params)
        super().__init__("ASDSteel1D", tag, *mat_params)

