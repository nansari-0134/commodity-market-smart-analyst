"""
Divergence & Statistical Anomaly Detection Core.

Detects decoupling between market observables:
- Price vs Open Interest divergence
- Price vs COT Managed Money positioning divergence
- Outright Price vs Forward Curve slope divergence
- Robust Median Absolute Deviation (MAD-Z) statistical spikes
"""
import numpy as np


def compute_mad_zscore(values: np.ndarray) -> float:
    """
    Compute robust z-score using Median Absolute Deviation (MAD).
    Insensitive to extreme historical outliers.
    
    Formula: (x - median) / (1.4826 * MAD)
    """
    if len(values) < 5:
        return 0.0
        
    med = float(np.median(values))
    mad = float(np.median(np.abs(values - med)))
    
    if mad == 0:
        return 0.0
        
    normalizer = 1.4826 * mad
    latest_val = float(values[-1])
    mad_z = float((latest_val - med) / normalizer)
    return round(mad_z, 2)


def detect_price_oi_divergence(
    prices: np.ndarray,
    open_interests: np.ndarray,
    lookback: int = 20,
) -> dict | None:
    """
    Detect divergence between price trends and open interest.
    Example: Price breaks out to 20-day highs while OI is plunging (short covering rally, not new buying).
    """
    n = min(len(prices), len(open_interests))
    if n < lookback:
        return None
        
    p = prices[-lookback:]
    oi = open_interests[-lookback:]
    
    p_ret = (p[-1] - p[0]) / p[0] if p[0] > 0 else 0
    oi_ret = (oi[-1] - oi[0]) / oi[0] if oi[0] > 0 else 0
    
    # Severe Divergence: Price rallying strongly (+5%) but OI dropping significantly (-5%)
    if p_ret >= 0.04 and oi_ret <= -0.04:
        return {
            "type": "PRICE_VS_OI_DIVERGENCE",
            "severity": "MODERATE",
            "description": f"Price rallied {p_ret*100:+.1f}% over {lookback}D but Open Interest fell {oi_ret*100:+.1f}% (indicates short-covering exhaustion rather than organic accumulation).",
        }
    elif p_ret <= -0.04 and oi_ret <= -0.04:
        return {
            "type": "PRICE_VS_OI_DIVERGENCE",
            "severity": "MILD",
            "description": f"Price declined {p_ret*100:+.1f}% alongside {oi_ret*100:+.1f}% OI reduction (indicates long liquidation rather than aggressive short-seller buildup).",
        }
        
    return None


def detect_price_cot_divergence(
    price_change_4w_pct: float,
    mm_net_change_contracts: int,
    commercial_net_change_contracts: int,
) -> dict | None:
    """
    Detect divergence between multi-week price move and institutional CFTC positioning.
    Example: Price up strongly but speculative funds actively selling into the rally.
    """
    # Price up > 3% but Managed Money sold > 10,000 contracts
    if price_change_4w_pct >= 0.03 and mm_net_change_contracts <= -10000:
        return {
            "type": "PRICE_VS_COT_DIVERGENCE",
            "severity": "SEVERE",
            "description": f"Price advanced {price_change_4w_pct*100:+.1f}% over 4 weeks, yet Managed Money net positioning declined by {abs(mm_net_change_contracts):,d} contracts (funds taking profits / bearish divergence).",
        }
    # Price down > 3% but Managed Money bought > 10,000 contracts
    elif price_change_4w_pct <= -0.03 and mm_net_change_contracts >= 10000:
        return {
            "type": "PRICE_VS_COT_DIVERGENCE",
            "severity": "MODERATE",
            "description": f"Price declined {price_change_4w_pct*100:+.1f}% over 4 weeks while Managed Money absorbed {mm_net_change_contracts:,d} net long contracts (bullish institutional divergence).",
        }
        
    return None


def detect_price_curve_divergence(
    price_change_20d_pct: float,
    prompt_spread_change: float,
    curve_state: str,
) -> dict | None:
    """
    Detect divergence between flat price and physical term structure slope.
    Example: Outright price rallying, but forward curve shifting from backwardation into contango
    (suggests prompt physical surplus despite financial speculative buying).
    """
    if price_change_20d_pct >= 0.04 and ("CONTANGO" in curve_state or prompt_spread_change < -0.50):
        return {
            "type": "OUTRIGHT_VS_CURVE_DIVERGENCE",
            "severity": "SEVERE",
            "description": f"Outright price rallied {price_change_20d_pct*100:+.1f}%, but the forward curve is in {curve_state} (prompt physical fundamentals lag financial price action).",
        }
        
    return None
