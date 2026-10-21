"""
Configuration schemas and default parameters for the Live Quantitative Feature Engine.

Defines lookback windows, timeframe definitions, indicator defaults,
thresholds, and benchmark relative-value pairs.
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Tuple


class Timeframe(str, Enum):
    M1 = "1m"
    M5 = "5m"
    M15 = "15m"
    H1 = "1h"
    H4 = "4h"
    D1 = "1D"


@dataclass(frozen=True)
class FeatureConfig:
    """Master parameter configuration for feature calculation."""
    # Lookback windows
    lookback_short: int = 20
    lookback_medium: int = 60
    lookback_long: int = 120
    lookback_annual: int = 252

    # Moving Average parameters
    ema_fast: int = 20
    ema_medium: int = 50
    ema_slow: int = 200

    # Momentum parameters
    rsi_period: int = 14
    macd_fast: int = 12
    macd_slow: int = 26
    macd_signal: int = 9

    # Volatility parameters
    atr_period: int = 14
    realized_vol_period: int = 20
    vol_annualization_factor: float = 252.0 ** 0.5  # ~15.8745 for daily

    # Trend & Strength parameters
    adx_period: int = 14
    adx_trend_threshold: float = 25.0
    adx_strong_trend_threshold: float = 40.0

    # Market Structure & Breakouts
    swing_pivot_window: int = 5
    breakout_atr_multiple: float = 1.5

    # Volume parameters
    rvol_window: int = 20
    volume_shock_z: float = 2.0

    # Benchmark Relative-Value Pairs (Commodity -> Benchmark Peer)
    relative_value_pairs: Dict[str, str] = field(default_factory=lambda: {
        "CL": "BRENT",
        "BRENT": "CL",
        "HO": "CL",      # Heating Oil / Diesel vs WTI
        "RB": "CL",      # RBOB Gasoline vs WTI
        "NG": "CL",      # Gas-to-Oil BTU ratio
        "GOLD": "SILVER",
        "SILVER": "GOLD",
        "COPPER": "GOLD",
        "CORN": "SOYBEANS",
        "SOYBEANS": "CORN",
        "WHEAT": "CORN",
    })

    # Default thresholds for scoring & regimes
    rsi_overbought: float = 70.0
    rsi_oversold: float = 30.0
    zscore_extreme_threshold: float = 2.0


DEFAULT_FEATURE_CONFIG = FeatureConfig()
