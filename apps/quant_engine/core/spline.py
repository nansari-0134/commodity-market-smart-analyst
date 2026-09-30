"""
Monotone Forward Curve Interpolation Core.

Uses Piecewise Cubic Hermite Interpolating Polynomials (PCHIP) from SciPy.
PCHIP guarantees:
- Monotonicity preservation: will never overshoot adjacent settlement prices
- C1 continuous derivative (smooth forward rate)
- No unphysical negative prices or oscillations between illiquid expiries
"""
import numpy as np
from scipy.interpolate import PchipInterpolator


def fit_forward_curve_spline(
    tenor_days: np.ndarray,
    contract_prices: np.ndarray,
) -> PchipInterpolator:
    """
    Fit a monotone cubic PCHIP interpolator across discrete forward contract tenors.
    
    Args:
        tenor_days: 1D array of days to contract expiry (must be strictly increasing, e.g. [15, 45, 75, ...]).
        contract_prices: 1D array of contract settlement prices.
        
    Returns:
        Fitted PchipInterpolator callable object.
    """
    if len(tenor_days) < 2:
        raise ValueError("At least 2 forward contract tenors are required to interpolate a forward curve.")
        
    # Sort by tenor days strictly
    sort_idx = np.argsort(tenor_days)
    days_sorted = tenor_days[sort_idx]
    prices_sorted = contract_prices[sort_idx]
    
    # Remove duplicate days if any
    unique_days, unique_idx = np.unique(days_sorted, return_index=True)
    unique_prices = prices_sorted[unique_idx]
    
    if len(unique_days) < 2:
        raise ValueError("Unique tenor count must be at least 2.")
        
    return PchipInterpolator(unique_days, unique_prices, extrapolate=True)


def sample_forward_curve(
    spline: PchipInterpolator,
    target_tenors: tuple[int, ...] = (0, 30, 60, 90, 180, 270, 360, 720),
) -> dict[str, float]:
    """
    Sample continuous price levels from the fitted spline for standard institutional tenors.
    
    Args:
        spline: Fitted PchipInterpolator.
        target_tenors: Days to evaluate (e.g. 0=spot/prompt, 30=1M, 60=2M, 360=1Y, 720=2Y).
        
    Returns:
        Dictionary mapping tenor labels to interpolated prices (e.g. {'prompt': 78.50, '1M': 78.10, ...}).
    """
    label_map = {
        0: "prompt",
        30: "1M",
        60: "2M",
        90: "3M",
        180: "6M",
        270: "9M",
        360: "12M",
        720: "24M",
    }
    
    sampled = {}
    for d in target_tenors:
        price = float(spline(d))
        label = label_map.get(d, f"{d}D")
        sampled[label] = round(price, 4)
        
    return sampled
