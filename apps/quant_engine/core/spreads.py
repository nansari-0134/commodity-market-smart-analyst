"""
Processing Spreads & Transformation Margins Core.

Calculates benchmark transformation spreads across energy and agriculture:
- 3:2:1 Refinery Crack Spread (Crude -> Gasoline + Distillate)
- 2:1:1 Heating Oil / ULSD Crack Spread
- Soybean Crush Spread (Soybeans -> Meal + Oil)
- Natural Gas Spark Spread (Gas -> Power)
"""


def compute_321_crack_spread(
    wti_crude_bbl: float,
    rbob_gasoline_gal: float,
    heating_oil_gal: float,
) -> float:
    """
    Compute 3:2:1 Refinery Crack Spread in $/barrel.
    
    A standard refinery yields approximately 2 barrels of gasoline and 1 barrel
    of distillate for every 3 barrels of crude oil processed.
    
    Args:
        wti_crude_bbl: WTI Crude prompt price in $/bbl (e.g. 78.50).
        rbob_gasoline_gal: RBOB Gasoline prompt price in $/gallon (e.g. 2.45).
                           If supplied in cents/gal (e.g. 245.0), automatically converted.
        heating_oil_gal: Heating Oil/ULSD prompt price in $/gallon (e.g. 2.65).
                         If supplied in cents/gal (e.g. 265.0), automatically converted.
                         
    Returns:
        Gross refinery margin in $/barrel.
    """
    # Auto-normalize cents/gal to $/gal if > 20
    gas_gal = rbob_gasoline_gal / 100.0 if rbob_gasoline_gal > 20.0 else rbob_gasoline_gal
    ho_gal = heating_oil_gal / 100.0 if heating_oil_gal > 20.0 else heating_oil_gal
    
    # 1 barrel = 42 US gallons
    gas_revenue = 2 * (gas_gal * 42.0)
    ho_revenue = 1 * (ho_gal * 42.0)
    crude_cost = 3 * wti_crude_bbl
    
    crack_321 = (gas_revenue + ho_revenue - crude_cost) / 3.0
    return round(float(crack_321), 2)


def compute_soybean_crush_spread(
    soybeans_bu: float,
    soybean_meal_ton: float,
    soybean_oil_lb: float,
) -> float:
    """
    Compute Board Soybean Crush Spread in $/bushel.
    
    1 bushel of soybeans (60 lbs) yields ~48 lbs (0.024 short tons, standard CME 0.022 multiplier)
    of soybean meal and ~11 lbs of soybean oil.
    
    Args:
        soybeans_bu: Soybean price in $/bushel or cents/bu (e.g. 11.50 or 1150).
        soybean_meal_ton: Soybean meal price in $/short ton (e.g. 340.0).
        soybean_oil_lb: Soybean oil price in cents/lb or $/lb (e.g. 46.50 cents/lb).
        
    Returns:
        Gross processor crush margin in $/bushel.
    """
    # Normalize beans to $/bu
    beans = soybeans_bu / 100.0 if soybeans_bu > 100.0 else soybeans_bu
    # Normalize oil: if in cents/lb (e.g. 46.5), convert to $/bushel using CME factor 0.11 ($/bu per cent/lb)
    # CME rule: 11 lbs of oil per bu -> 1 cent/lb = $0.11/bu
    if soybean_oil_lb > 1.0:
        oil_rev = soybean_oil_lb * 0.11
    else:
        oil_rev = (soybean_oil_lb * 100.0) * 0.11
        
    # Meal factor: 44 lbs / 2000 lbs = 0.022 tons per bushel
    meal_rev = soybean_meal_ton * 0.022
    
    crush_margin = (meal_rev + oil_rev) - beans
    return round(float(crush_margin), 2)


def compute_spark_spread(
    power_price_mwh: float,
    natural_gas_mmbtu: float,
    heat_rate_btu_kwh: float = 7000.0,
) -> float:
    """
    Compute Spark Spread in $/MWh for natural gas combined-cycle power generation.
    
    Formula: Power ($/MWh) - [Natural Gas ($/MMBtu) * Heat Rate / 1000]
    """
    fuel_cost = natural_gas_mmbtu * (heat_rate_btu_kwh / 1000.0)
    spark_spread = power_price_mwh - fuel_cost
    return round(float(spark_spread), 2)
