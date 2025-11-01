from apeSees.materials.base import Material

# Assuming apeSees.materials.base is available in the Python path
# (Content from nmorabowen/apesees/apeSees-66420558d9652ba95ba906ae9714dfd264cf6608/src/apeSees/materials/base.py)

class Concrete01(Material):
    """
    Represents the OpenSees Concrete01 uniaxial material.

    This is the Kent-Scott-Park concrete model with degraded linear
    unloading/reloading stiffness and no tensile strength.

    OpenSees Documentation Parameters [1.1, 1.3, 1.5]:
    matTag, fpc, epsc0, fpcu, epsU
    
    Parameters
    ----------
    tag : int
        Unique material tag.
    fpc : float
        Concrete compressive strength (must be a negative value).
    epsc0 : float
        Concrete strain at maximum strength (must be a negative value).
    fpcu : float
        Concrete crushing strength (must be a negative value).
    epsu : float
        Concrete strain at crushing strength (must be a negative value).
    """
    def __init__(self,
                 tag: int,
                 fpc: float,
                 epsc0: float,
                 fpcu: float,
                 epsu: float):
        
        # Check that compressive values are negative, as required
        if fpc > 0:
            print(f"Warning: fpc ({fpc}) should be negative. Converting.")
            fpc = -fpc
        if epsc0 > 0:
            print(f"Warning: epsc0 ({epsc0}) should be negative. Converting.")
            epsc0 = -epsc0
        if fpcu > 0:
             print(f"Warning: fpcu ({fpcu}) is positive. 
                   It's usually zero or negative. Converting.")
             fpcu = -fpcu
        if epsu > 0:
            print(f"Warning: epsu ({epsu}) should be negative. Converting.")
            epsu = -epsu
        if fpcu > fpc:
            print(f"Warning: Crushing strength fpcu ({fpcu}) is greater 
                  than max strength fpc ({fpc}).")
        if epsu < epsc0:
            print(f"Warning: Crushing strain epsu ({epsu}) is less than 
                  strain at max strength epsc0 ({epsc0}).")


        # Collect all parameters in the exact positional order
        mat_params = [fpc, epsc0, fpcu, epsu]

        # Call the parent class __init__
        # It expects (mat_type, tag, *params)
        super().__init__("Concrete01", tag, *mat_params)

