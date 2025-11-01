from apeSees.materials.base import Material
from typing import Optional, List, Tuple

# Assuming apeSees.materials.base is available in the Python path
# (Content from nmorabowen/apesees/apeSees-66420558d9652ba95ba906ae9714dfd264cf6608/src/apeSees/materials/base.py)

class ASDConcrete1D(Material):
    """
    Represents the OpenSees ASDConcrete1D uniaxial material.

    This is a plastic-damage model for concrete and masonry-like materials,
    with optional IMPL-EX integration and regularization.

    OpenSees Documentation Parameters:
    uniaxialMaterial ASDConcrete1D $tag $E <-fc $fc> <-ft $ft>
                             <-Te $Te -Ts $Ts <-Td $Td>> 
                             <-Ce $Ce -Cs $Cs <-Cd $Cd>> 
                             <-implex> 
                             <-implexControl $err $lim> 
                             <-implexAlpha $alpha> 
                             <-eta $eta> 
                             <-tangent> 
                             <-autoRegularization $lch_ref>
    
    Parameters
    ----------
    tag : int
        Unique material tag.
    e : float
        Young's modulus (Mandatory).
    fc : float, optional
        Concrete compressive strength (e.g., -30.0).
    ft : float, optional
        Concrete tensile strength (e.g., 3.0).
    te : List[float], optional
        List of total-strain values for the tensile backbone.
    ts : List[float], optional
        List of stress values for the tensile backbone.
    td : List[float], optional
        List of damage values for the tensile backbone.
    ce : List[float], optional
        List of total-strain values for the compressive backbone.
    cs : List[float], optional
        List of stress values for the compressive backbone.
    cd : List[float], optional
        List of damage values for the compressive backbone.
    implex : bool, optional
        If True, activates the IMPL-EX integration scheme. (Default: False)
    implex_control : Tuple[float, float], optional
        (implexErrorTolerance, implexTimeReductionLimit)
    implex_alpha : float, optional
        Alpha coefficient for IMPL-EX (Default: 1.0 in OpenSees).
    eta : float, optional
        Viscosity parameter for rate-dependent model.
    tangent : bool, optional
        If True, uses the tangent constitutive matrix (Default: False, uses secant).
    auto_regularization : float, optional
        Activates regularization. Pass the characteristic length (lch_ref).
    """
    def __init__(self,
                 tag: int,
                 e: float,
                 fc: Optional[float] = None,
                 ft: Optional[float] = None,
                 te: Optional[List[float]] = None,
                 ts: Optional[List[float]] = None,
                 td: Optional[List[float]] = None,
                 ce: Optional[List[float]] = None,
                 cs: Optional[List[float]] = None,
                 cd: Optional[List[float]] = None,
                 implex: bool = False,
                 implex_control: Optional[Tuple[float, float]] = None,
                 implex_alpha: Optional[float] = None,
                 eta: Optional[float] = None,
                 tangent: bool = False,
                 auto_regularization: Optional[float] = None):
        
        # Start with mandatory positional parameter
        mat_params = [e]
        
        # --- Add optional keyword parameters ---
        
        if fc is not None:
            mat_params.extend(["-fc", fc])
            
        if ft is not None:
            mat_params.extend(["-ft", ft])

        # Tensile backbone
        if te is not None:
            mat_params.extend(["-Te", te])
        if ts is not None:
            mat_params.extend(["-Ts", ts])
        if td is not None:
            mat_params.extend(["-Td", td])
            
        # Compressive backbone
        if ce is not None:
            mat_params.extend(["-Ce", ce])
        if cs is not None:
            mat_params.extend(["-Cs", cs])
        if cd is not None:
            mat_params.extend(["-Cd", cd])

        # Flags and other keywords
        if implex:
            mat_params.append("-implex")
            
        if implex_control is not None:
            mat_params.extend(["-implexControl", implex_control[0], implex_control[1]])
            
        if implex_alpha is not None:
            mat_params.extend(["-implexAlpha", implex_alpha])
            
        if eta is not None:
            mat_params.extend(["-eta", eta])
            
        if tangent:
            mat_params.append("-tangent")
            
        if auto_regularization is not None:
            mat_params.extend(["-autoRegularization", auto_regularization])

        # Call the parent class __init__
        # It expects (mat_type, tag, *params)
        super().__init__("ASDConcrete1D", tag, *mat_params)

