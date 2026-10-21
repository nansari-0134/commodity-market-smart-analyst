"""
Pydantic v2 strict schemas for the Live Quantitative Feature Engine.

Directly implements Section 21 of the specification:
Produces compact, normalized, relative, and interpretable features
tailored for downstream Financial Research LLM synthesis (Phase 13).
"""
from datetime import datetime
from typing import Dict, List, Literal, Optional
from pydantic import BaseModel, Field


class PriceFeatures(BaseModel):
    last: float = Field(..., description="Current prompt settlement/last price")
    return_1m: Optional[float] = Field(default=None, description="1-minute return if high-frequency tick feed active")
    return_5m: Optional[float] = Field(default=None, description="5-minute return if high-frequency tick feed active")
    return_15m: Optional[float] = Field(default=None, description="15-minute return")
    return_1h: Optional[float] = Field(default=None, description="1-hour return")
    return_1d: float = Field(..., description="1-day return (close-to-close or live-to-close)")
    log_return_1d: float = Field(..., description="1-day continuous log return: ln(P_t / P_t-1)")
    return_acceleration_1d: float = Field(default=0.0, description="Change in daily return vs prior day: r_t - r_t-1")
    percentile_20d: float = Field(..., description="Price percentile within rolling 20-day window [0-100]")
    zscore_20d: float = Field(..., description="Price Z-score within rolling 20-day distribution")


class TrendFeatures(BaseModel):
    ema_structure: Literal["bullish", "bearish", "neutral"] = Field(..., description="EMA ordering state (fast > med > slow)")
    ema_slope: Literal["positive", "negative", "flat"] = Field(..., description="Direction of short-term EMA")
    adx: float = Field(..., description="14-period Average Directional Index [0-100]")
    trend_state: Literal["strong_bullish", "weak_bullish", "ranging", "weak_bearish", "strong_bearish"] = Field(
        ..., description="Composite trend and strength regime"
    )
    dist_ema20_pct: float = Field(..., description="% distance from 20-day EMA: (Price - EMA20) / EMA20 * 100")
    dist_ema50_pct: float = Field(..., description="% distance from 50-day EMA: (Price - EMA50) / EMA50 * 100")
    dist_ema200_pct: float = Field(..., description="% distance from 200-day EMA: (Price - EMA200) / EMA200 * 100")


class MomentumFeatures(BaseModel):
    rsi: float = Field(..., description="14-period Relative Strength Index [0-100]")
    rsi_percentile: float = Field(..., description="RSI percentile rank over 60-day historical window [0-100]")
    rsi_direction: Literal["rising", "falling", "flat"] = Field(..., description="Direction of RSI change over last 3 periods")
    macd: float = Field(..., description="MACD Line (12 EMA - 26 EMA)")
    macd_signal: float = Field(..., description="Signal Line (9 EMA of MACD)")
    macd_histogram: float = Field(..., description="MACD Histogram (MACD - Signal)")
    histogram_direction: Literal["increasing", "decreasing", "flat"] = Field(..., description="Histogram delta direction")
    momentum_state: Literal["strengthening", "weakening", "overbought", "oversold", "neutral"] = Field(
        ..., description="Momentum regime"
    )


class VolatilityFeatures(BaseModel):
    atr: float = Field(..., description="14-period Average True Range in price units")
    atr_pct: float = Field(..., description="ATR as a percentage of spot price")
    atr_percentile: float = Field(..., description="ATR percentile rank over 60-day window [0-100]")
    realized_volatility: float = Field(..., description="Annualized realized volatility in % (20-day rolling)")
    vol_percentile: float = Field(..., description="Realized volatility percentile vs 1-year distribution [0-100]")
    regime: Literal["low", "normal", "high", "extreme"] = Field(..., description="Volatility regime")


class VolumeFeatures(BaseModel):
    volume: int = Field(..., description="Latest session volume")
    relative_volume: float = Field(..., description="RVOL: Volume / 20-day moving average volume")
    zscore: float = Field(..., description="Volume Z-score vs 20-day distribution")
    state: Literal["unusually_low", "low", "normal", "high", "unusually_high"] = Field(..., description="Participation state")


class StructureFeatures(BaseModel):
    state: Literal["bullish_breakout", "bearish_breakdown", "range_bound", "testing_resistance", "testing_support", "normal"] = Field(
        ..., description="Structural classification"
    )
    range_position_20d: float = Field(..., description="Position inside 20D high-low range: (Price - Low)/(High - Low) * 100")
    range_position_60d: float = Field(..., description="Position inside 60D high-low range [0-100]")
    nearest_resistance_distance_pct: float = Field(..., description="% distance to nearest major resistance level")
    nearest_support_distance_pct: float = Field(..., description="% distance to nearest major support level")
    nearest_resistance: float = Field(..., description="Nearest resistance price level")
    nearest_support: float = Field(..., description="Nearest support price level")
    swing_structure: Literal["higher_highs_higher_lows", "lower_highs_lower_lows", "range", "transition"] = Field(
        ..., description="Recent swing high/low classification"
    )
    breakout_confirmed: bool = Field(default=False, description="True if price broke swing level with ATR confirmation")


class VwapFeatures(BaseModel):
    vwap: float = Field(..., description="Volume-Weighted Average Price")
    vwap_deviation_pct: float = Field(..., description="% deviation: (Price - VWAP) / VWAP * 100")


class CurveFeatures(BaseModel):
    spread_f1_f2: float = Field(default=0.0, description="Front to prompt+1 spread (F1 - F2)")
    spread_f2_f3: float = Field(default=0.0, description="Second to third month spread (F2 - F3)")
    spread_f1_f3: float = Field(default=0.0, description="Front to third month spread (F1 - F3)")
    spread_zscore: float = Field(default=0.0, description="Rolling 60-day Z-score of F1-F2 spread")
    spread_percentile: float = Field(default=50.0, description="Percentile rank of F1-F2 spread [0-100]")
    curve_state: Literal["strong_backwardation", "backwardation", "flat", "contango", "strong_contango"] = Field(
        default="flat", description="Futures curve term structure classification"
    )
    curve_slope_annualized: float = Field(default=0.0, description="Annualized term structure slope (F12 - F1)/F1")


class RelativeValueFeatures(BaseModel):
    benchmark_pair: str = Field(default="", description="Key benchmark economic pair (e.g. 'CL-BRENT', 'GOLD-SILVER')")
    rolling_correlation: float = Field(default=0.0, description="60-day rolling Pearson correlation with benchmark")
    spread_zscore: float = Field(default=0.0, description="Relative-value spread/ratio Z-score vs 60-day mean")


class OrderFlowFeatures(BaseModel):
    imbalance: Optional[float] = Field(default=None, description="Buy/Sell volume imbalance ratio (-1.0 to +1.0)")
    cumulative_delta: Optional[float] = Field(default=None, description="Cumulative aggressive delta in contracts")
    delta_direction: Literal["aggressive_buying", "aggressive_selling", "neutral", "unavailable"] = Field(
        default="unavailable", description="Order flow delta regime"
    )
    is_available: bool = Field(default=False, description="Whether reliable tick/order-book feed is active")


class LiquidityFeatures(BaseModel):
    bid_ask_spread: Optional[float] = Field(default=None, description="Top-of-book bid-ask spread in currency units")
    bid_ask_spread_ticks: Optional[float] = Field(default=None, description="Bid-ask spread in exchange minimum ticks")
    spread_percentile: Optional[float] = Field(default=None, description="Spread percentile rank vs 20-day distribution")
    depth_imbalance: Optional[float] = Field(default=None, description="L2 Book depth imbalance: (Bid - Ask)/(Bid + Ask)")
    is_available: bool = Field(default=False, description="Whether L1/L2 liquidity feed is active")


class FundamentalsFeatures(BaseModel):
    primary_variable: Optional[str] = Field(default=None, description="Key inventory or balance metric (e.g. 'CRUDE_CUSHING_STOCKS')")
    latest_value: Optional[float] = Field(default=None, description="Latest official survey release value")
    normal_reference: Optional[float] = Field(default=None, description="5-year seasonal normal reference value")
    deviation_abs: Optional[float] = Field(default=None, description="Absolute deviation: Value - Reference")
    deviation_pct: Optional[float] = Field(default=None, description="Percentage deviation from seasonal normal")
    inventory_zscore: Optional[float] = Field(default=None, description="Z-score vs 5-year seasonal distribution")
    fundamental_momentum: Literal["tightening", "loosening", "building", "drawing", "neutral", "unavailable"] = Field(
        default="unavailable", description="Physical supply/demand balance trajectory"
    )


class EventsFeatures(BaseModel):
    latest_event: Optional[str] = Field(default=None, description="Latest macroeconomic or commodity release name")
    surprise: Optional[float] = Field(default=None, description="Raw economic surprise: Actual - Forecast")
    standardized_surprise: Optional[float] = Field(default=None, description="Standardized surprise z-score")
    immediate_reaction_1h_pct: Optional[float] = Field(default=None, description="Immediate 1-hour price reaction in %")
    reaction_volatility_pct: Optional[float] = Field(default=None, description="1-hour realized volatility expansion in %")


class RegimeFeatures(BaseModel):
    trend: str = Field(..., description="Trend regime state (e.g. 'strong_bullish', 'ranging')")
    volatility: str = Field(..., description="Volatility regime state (e.g. 'high', 'normal')")
    overall: str = Field(..., description="Combined composite regime (e.g. 'bullish_high_volatility')")


class DivergenceDetail(BaseModel):
    divergence_type: Literal["price_vs_rsi", "price_vs_volume", "price_vs_oi", "price_vs_order_flow"] = Field(
        ..., description="Indicator pair"
    )
    direction: Literal["bullish", "bearish"] = Field(..., description="Divergence bias")
    severity: Literal["mild", "moderate", "strong"] = Field(..., description="Statistical divergence strength")
    timeframe: str = Field(default="1D", description="Observed timeframe")
    description: str = Field(..., description="Human-readable divergence explanation")


class DivergenceFeatures(BaseModel):
    has_divergence: bool = Field(default=False, description="Whether any statistically valid divergence is active")
    active_divergences: List[DivergenceDetail] = Field(default_factory=list, description="Active divergence findings")


class QuantitativeScores(BaseModel):
    trend_score: float = Field(..., description="Normalized trend direction & strength [-1.0 to +1.0]")
    momentum_score: float = Field(..., description="Normalized momentum acceleration [-1.0 to +1.0]")
    volatility_score: float = Field(..., description="Normalized volatility expansion score [0.0 to 1.0]")
    volume_score: float = Field(..., description="Normalized volume participation score [0.0 to 1.0]")
    structure_score: float = Field(..., description="Normalized market structure score [-1.0 to +1.0]")
    curve_score: float = Field(..., description="Normalized futures curve term structure score [-1.0 to +1.0]")
    relative_value_score: float = Field(..., description="Normalized relative-value valuation score [-1.0 to +1.0]")
    fundamentals_score: float = Field(..., description="Normalized physical supply tightness score [-1.0 to +1.0]")
    event_score: float = Field(..., description="Normalized event impact score [-1.0 to +1.0]")
    overall_composite_score: float = Field(..., description="Master composite quantitative rating [-1.0 to +1.0]")


class LiveQuantFeaturePackage(BaseModel):
    """
    Master LLM-Ready Quantitative Feature Package.
    Compact, normalized, and interpretable representation of current market state.
    """
    instrument: str = Field(..., description="Canonical commodity code (e.g. 'CL', 'BRENT', 'NG')")
    name: str = Field(..., description="Full commodity name")
    sector: str = Field(..., description="Sector classification (ENERGY, METALS, AGRICULTURE)")
    timestamp: str = Field(..., description="UTC ISO-8601 generation timestamp")
    timeframe: str = Field(default="1D", description="Evaluation timeframe")
    data_quality: str = Field(default="VALID", description="Overall data quality status (VALID, STALE, INSUFFICIENT_HISTORY)")
    
    # 13 Structured Analytical Sub-Models
    price: PriceFeatures
    trend: TrendFeatures
    momentum: MomentumFeatures
    volatility: VolatilityFeatures
    volume: VolumeFeatures
    structure: StructureFeatures
    vwap: VwapFeatures
    curve: CurveFeatures
    relative_value: RelativeValueFeatures
    order_flow: OrderFlowFeatures
    liquidity: LiquidityFeatures
    fundamentals: FundamentalsFeatures
    events: EventsFeatures
    regime: RegimeFeatures
    divergence: DivergenceFeatures
    scores: QuantitativeScores
