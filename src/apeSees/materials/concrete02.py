from apeSees.materials.base import Material

# Assuming apeSees.materials.base is available in the Python path
# (Content from nmorabowen/apesees/apeSees-66420558d9652ba95ba906ae9714dfd264cf6608/src/apeSees/materials/base.py)

class Concrete02(Material):
    """
    Represents the OpenSees Concrete02 uniaxial material.

    This is a concrete model with linear tension softening. It uses the
    Kent-Scott-Park model for compression (like Concrete01) but adds
    a linear descending branch in tension.

    OpenSees Documentation Parameters [1.1, 1.2, 1.4]:
    matTag, fpc, epsc0, fpcu, epsU, lambda, ft, Ets
    
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
    lambda_val : float
        Ratio between unloading slope at epsU and initial slope (positive).
    ft : float
        Tensile strength (must be a positive value).
    ets : float
        Tension softening stiffness (must be a positive value).
    """
    def __init__(self,
                 tag: int,
                 fpc: float,
                 epsc0: float,
                 fpcu: float,
                 epsu: float,
                 lambda_val: float,
                 ft: float,
                 ets: float):
        
        # --- Validate Compressive Parameters (Negative) ---
        if fpc > 0:
            print(f"Warning: fpc ({fpc}) should be negative. Converting.")
            fpc = -fpc
        if epsc0 > 0:
            print(f"Warning: epsc0 ({epsc0}) should be negative. Converting.")
            epsc0 = -epsc0
        if fpcu > 0:
             print(f"Warning: fpcu ({fpcu}) is positive. It's usually zero or negative. Converting.")
             fpcu = -fpcu
        if epsu > 0:
            print(f"Warning: epsu ({epsu}) should be negative. Converting.")
            epsu = -epsu

        # --- Validate Tensile Parameters (Positive) ---
        if lambda_val < 0:
            print(f"Warning: lambda_val ({lambda_val}) should be positive. Converting.")
            lambda_val = abs(lambda_val)
        if ft < 0:
            print(f"Warning: ft ({ft}) should be positive. Converting.")
            ft = abs(ft)
        if ets < 0:
            print(f"Warning: ets ({ets}) should be positive. Converting.")
            ets = abs(ets)

        # Collect all parameters in the exact positional order
        mat_params = [fpc, epsc0, fpcu, epsu, lambda_val, ft, ets]

        # Call the parent class __init__
        # It expects (mat_type, tag, *params)
        super().__init__("Concrete02", tag, *mat_params)

