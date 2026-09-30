"""
Vectorized Market-State Construction Core.

Pure Python + NumPy calculation routines (ZERO Django ORM dependencies).
Enforces Section 5.1 of Master Architecture:
- Multi-horizon returns (1D, 5D, 21D, 63D, 252D)
- True Range & Normalized ATR (14-period)
- Close-to-close & Garman-Klass high-efficiency realized volatility
- Relative Volume (RVOL) & volume shock z-scores
- Open Interest flow regimes & interaction quadrants
"""
import numpy as np


def compute_returns(prices: np.ndarray, horizons: tuple[int, ...] = (1, 5, 21, 63, 252)) -> dict[str, float]:
    """
    Compute multi-horizon percentage returns from an ordered price array.
    
    Args:
        prices: 1D array of historical prices, ordered chronologically (latest is last).
        horizons: Lookback horizons in trading days.
        
    Returns:
        Dictionary mapping horizon keys to percentage returns (e.g. {'returns_1d': 0.015}).
    """
    n = len(prices)
    results = {}
    
    for h in horizons:
        key = f"returns_{h}d"
        if n > h and prices[-1 - h] > 0:
            ret = float((prices[-1] - prices[-1 - h]) / prices[-1 - h])
        else:
            ret = 0.0
        results[key] = round(ret, 6)
        
    return results


def compute_realized_volatility(close_prices: np.ndarray, windows: tuple[int, ...] = (20, 60)) -> dict[str, float]:
    """
    Compute annualized close-to-close realized volatility in percent.
    Formula: std(log_returns) * sqrt(252) * 100.
    """
    results = {}
    if len(close_prices) < 2:
        return {f"realized_vol_{w}d": 0.0 for w in windows}
        
    log_returns = np.diff(np.log(close_prices))
    
    for w in windows:
        key = f"realized_vol_{w}d"
        if len(log_returns) >= w:
            window_returns = log_returns[-w:]
            ann_vol = float(np.std(window_returns, ddof=1) * np.sqrt(252) * 100)
        elif len(log_returns) > 1:
            ann_vol = float(np.std(log_returns, ddof=1) * np.sqrt(252) * 100)
        else:
            ann_vol = 0.0
        results[key] = round(ann_vol, 2)
        
    return results


def compute_garman_klass_volatility(
    opens: np.ndarray,
    highs: np.ndarray,
    lows: np.ndarray,
    closes: np.ndarray,
    window: int = 20,
) -> float:
    """
    Compute annualized Garman-Klass volatility (incorporating open, high, low, close).
    Provides up to 8x higher statistical efficiency than close-to-close volatility.
    
    Formula: 0.5 * ln(H/L)^2 - (2*ln(2) - 1) * ln(C/O)^2
    """
    n = min(len(opens), len(highs), len(lows), len(closes))
    if n < 2:
        return 0.0
        
    o = opens[-window:]
    h = highs[-window:]
    l = lows[-window:]
    c = closes[-window:]
    
    # Avoid log(0) or division by zero
    valid_mask = (o > 0) & (h > 0) & (l > 0) & (c > 0) & (h >= l)
    if np.sum(valid_mask) < 2:
        return 0.0
        
    hl = np.log(h[valid_mask] / l[valid_mask])
    co = np.log(c[valid_mask] / o[valid_mask])
    
    gk_var = 0.5 * (hl ** 2) - (2 * np.log(2) - 1) * (co ** 2)
    mean_var = np.maximum(np.mean(gk_var), 0.0)
    
    ann_gk_vol = float(np.sqrt(mean_var * 252) * 100)
    return round(ann_gk_vol, 2)


def compute_atr(
    highs: np.ndarray,
    lows: np.ndarray,
    closes: np.ndarray,
    period: int = 14,
) -> tuple[float, float]:
    """
    Compute Average True Range (ATR) and normalized ATR (% of latest close).
    
    True Range = max(H - L, |H - C_prev|, |L - C_prev|)
    """
    n = min(len(highs), len(lows), len(closes))
    if n < 2:
        return 0.0, 0.0
        
    h = highs[-period - 1:]
    l = lows[-period - 1:]
    c = closes[-period - 1:]
    
    tr1 = h[1:] - l[1:]
    tr2 = np.abs(h[1:] - c[:-1])
    tr3 = np.abs(l[1:] - c[:-1])
    
    true_ranges = np.maximum(tr1, np.maximum(tr2, tr3))
    atr = float(np.mean(true_ranges[-period:]))
    
    latest_close = float(closes[-1])
    atr_pct = float((atr / latest_close) * 100) if latest_close > 0 else 0.0
    
    return round(atr, 4), round(atr_pct, 2)


def compute_volume_metrics(volumes: np.ndarray, window: int = 20) -> tuple[float, float]:
    """
    Compute Relative Volume (RVOL) and volume shock z-score against 20-day moving average.
    
    Returns:
        (rvol, volume_shock_z)
    """
    if len(volumes) < 2:
        return 1.0, 0.0
        
    recent_vols = volumes[-window:]
    mean_vol = float(np.mean(recent_vols[:-1])) if len(recent_vols) > 1 else float(volumes[-1])
    std_vol = float(np.std(recent_vols[:-1], ddof=1)) if len(recent_vols) > 2 else 0.0
    
    latest_vol = float(volumes[-1])
    
    rvol = float(latest_vol / mean_vol) if mean_vol > 0 else 1.0
    z_score = float((latest_vol - mean_vol) / std_vol) if std_vol > 0 else 0.0
    
    return round(rvol, 2), round(z_score, 2)


def classify_oi_regime(price_change_5d: float, oi_change_5d: float) -> str:
    """
    Classify Price/OI interaction quadrant based on 5-day changes.
    
    - Price Up + OI Up: Long Accumulation (Bullish continuation)
    - Price Up + OI Down: Short Covering (Weak rally, bears covering)
    - Price Down + OI Up: Short Accumulation (Bearish continuation)
    - Price Down + OI Down: Long Liquidation (Weak selloff, bulls capitulating)
    """
    threshold = 0.002  # 0.2% change threshold
    
    if price_change_5d > threshold and oi_change_5d > threshold:
        return "LONG_ACCUMULATION"
    elif price_change_5d > threshold and oi_change_5d < -threshold:
        return "SHORT_COVERING"
    elif price_change_5d < -threshold and oi_change_5d > threshold:
        return "SHORT_ACCUMULATION"
    elif price_change_5d < -threshold and oi_change_5d < -threshold:
        return "LONG_LIQUIDATION"
    else:
        return "NEUTRAL"
