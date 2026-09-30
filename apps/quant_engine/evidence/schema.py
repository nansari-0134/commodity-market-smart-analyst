"""
Strict Pydantic v2 Schema for the Quantitative Evidence Package.

Adheres strictly to Section 5.12 of the Master Architecture:
- Machine-readable intermediate communication between Python Quant and LLMs
- Zero LLM mental math: all statistics, slopes, spreads, and percentiles pre-calculated
- Explicit provenance and data quality metadata (Section 15)
"""
from datetime import datetime, date
from typing import Literal
from pydantic import BaseModel, Field


class MarketStateEvidence(BaseModel):
    """Core market price structure, volatility, volume, and open interest metrics."""
    spot_price: float = Field(..., description="Prompt front-month settlement price")
    returns_1d: float = Field(..., description="1-day percentage price change")
    returns_5d: float = Field(..., description="5-day percentage price change")
    returns_21d: float = Field(..., description="21-day (1M) percentage price change")
    returns_63d: float = Field(..., description="63-day (3M) percentage price change")
    returns_252d: float = Field(..., description="252-day (1Y) percentage price change")
    
    # Volatility
    realized_vol_20d: float = Field(..., description="20-day annualized close-to-close volatility in %")
    realized_vol_60d: float = Field(..., description="60-day annualized close-to-close volatility in %")
    garman_klass_vol_20d: float = Field(..., description="20-day Garman-Klass high-efficiency volatility in %")
    atr_14: float = Field(..., description="14-day Average True Range in price units")
    atr_pct: float = Field(..., description="14-day ATR as a percentage of spot price")
    
    # Volume & Liquidity
    rvol: float = Field(..., description="Relative Volume: today volume vs 20-day moving average")
    volume_shock_z: float = Field(..., description="Z-score of today volume vs 20-day distribution")
    
    # Open Interest & Positioning Flow
    open_interest: int | None = Field(default=None, description="Current total open interest")
    oi_change_1d_pct: float = Field(default=0.0, description="1-day percentage change in Open Interest")
    oi_change_5d_pct: float = Field(default=0.0, description="5-day percentage change in Open Interest")
    oi_regime: Literal["LONG_ACCUMULATION", "SHORT_COVERING", "SHORT_ACCUMULATION", "LONG_LIQUIDATION", "NEUTRAL"] = Field(
        default="NEUTRAL",
        description="Price/OI interaction quadrant",
    )
    
    # Curve & Term Structure
    curve_state: Literal["STRONG_BACKWARDATION", "MILD_BACKWARDATION", "FLAT", "MILD_CONTANGO", "STRONG_CONTANGO"] = Field(
        default="FLAT",
        description="Forward curve term structure slope",
    )
    prompt_spread_1m_2m: float = Field(default=0.0, description="Price difference between M1 prompt and M2 forward contract")
    roll_yield_1y: float = Field(default=0.0, description="Annualized roll yield: (M1 - M12) / M1 in %")
    butterfly_curvature: float = Field(default=0.0, description="Fly curvature: 2*M2 - (M1 + M3)")


class FundamentalStateEvidence(BaseModel):
    """Physical commodity balances, storage draws, and seasonal inventory percentiles."""
    storage_name: str | None = Field(default=None, description="Primary inventory metric (e.g. Cushing Crude Stocks)")
    storage_level: float | None = Field(default=None, description="Current reported inventory level")
    storage_unit: str | None = Field(default=None, description="Inventory unit of measure (e.g. MBBL, BCF)")
    storage_change_1w: float | None = Field(default=None, description="1-week net storage build/draw")
    seasonal_percentile: float | None = Field(default=None, description="Inventory level percentile vs 5-year seasonal norm")
    balance_regime: Literal["DEFICIT_DRAW", "BALANCED", "SURPLUS_BUILD", "UNAVAILABLE"] = Field(
        default="UNAVAILABLE",
        description="Physical balance trend",
    )


class COTPositioningEvidence(BaseModel):
    """Disaggregated CFTC Commitment of Traders positioning metrics."""
    money_manager_net: int = Field(default=0, description="Managed Money (speculative funds) Long minus Short contracts")
    money_manager_net_pct_oi: float = Field(default=0.0, description="Managed Money Net as % of Total Open Interest")
    commercial_net: int = Field(default=0, description="Commercial hedger (producer/merchant/swap) net positioning")
    commercial_net_pct_oi: float = Field(default=0.0, description="Commercial Net as % of Total Open Interest")
    crowding_regime: Literal["EXTREME_LONG", "MODERATE_LONG", "NEUTRAL", "MODERATE_SHORT", "EXTREME_SHORT"] = Field(
        default="NEUTRAL",
        description="Speculative fund positioning crowding state",
    )


class SpreadsEvidence(BaseModel):
    """Transformation margins, refinery cracks, and inter-commodity processing spreads."""
    crack_321: float | None = Field(default=None, description="3:2:1 Refinery Crack Spread ($/bbl)")
    crack_321_zscore_1y: float | None = Field(default=None, description="1-year z-score of 3:2:1 crack margin")
    crush_spread: float | None = Field(default=None, description="Soybean crush spread ($/bushel)")
    spark_spread: float | None = Field(default=None, description="Natural gas to power spark spread")


class CointegrationPairFinding(BaseModel):
    """Statistical cointegration test finding between two commodities."""
    pair: str = Field(..., description="Commodity pair code (e.g. 'CL-BRENT')")
    hedge_ratio_beta: float = Field(..., description="OLS cointegration hedge ratio (beta)")
    adf_t_statistic: float = Field(..., description="Augmented Dickey-Fuller residual test statistic")
    p_value: float = Field(..., description="ADF stationarity p-value")
    is_cointegrated: bool = Field(..., description="Whether residuals are stationary (p < 0.05)")
    half_life_days: float | None = Field(default=None, description="Ornstein-Uhlenbeck mean-reversion half life in trading days")
    residual_zscore: float = Field(..., description="Current residual spread z-score from equilibrium")
    status: Literal["MEAN_REVERSION_CANDIDATE", "EQUILIBRIUM", "DIVERGENT", "UNSTABLE"] = Field(
        default="EQUILIBRIUM",
        description="Trading research classification",
    )


class CrossCommodityEvidence(BaseModel):
    """Vectorized cross-commodity correlations, logical complexes, and macro transmission."""
    primary_complex: str = Field(..., description="Logical commodity complex name (e.g. 'REFINERY_ENERGY_COMPLEX')")
    complex_members: list[str] = Field(default_factory=list, description="Constituent commodities in this complex")
    key_spreads: dict[str, float] = Field(default_factory=dict, description="Active price spreads within the complex")
    cointegration_pairs: list[CointegrationPairFinding] = Field(default_factory=list, description="Validated cointegrating relationships")
    rolling_correlations: dict[str, float] = Field(default_factory=dict, description="60-day rolling correlations with peer commodities")
    macro_factor_sensitivities: dict[str, float] = Field(
        default_factory=dict,
        description="Sensitivities to macro factors: DXY, Real Rates (TIPS), Crude-Sugar, Crude-Corn",
    )


class DirectionalSeasonalTendency(BaseModel):
    """Statistically validated directional pattern for specific calendar tenures."""
    tenure_window: str = Field(..., description="Tenure window name (e.g. 'FORWARD_30D', 'SPRING_DRIVING_BUILD')")
    win_rate: float = Field(..., description="Historical win rate (fraction of years with positive return, e.g. 0.80)")
    median_return: float = Field(..., description="Median return over this window across historical years")
    mean_return: float = Field(..., description="Mean return over this window")
    t_statistic: float = Field(..., description="t-statistic testing if mean return differs significantly from 0")
    pattern_classification: str = Field(..., description="Qualitative pattern description")


class ForwardVolatilityPeak(BaseModel):
    """Historical expectation of realized volatility over the next 30 calendar days."""
    forward_expected_vol_30d: float = Field(..., description="Historical median forward 30-day realized volatility in %")
    percentile_vs_annual: float = Field(..., description="Forward volatility percentile vs full annual distribution (0-100)")
    is_peak_volatility_window: bool = Field(..., description="Flag indicating upcoming month is a peak historical volatility regime")
    seasonal_catalyst: str = Field(default="", description="Physical catalyst (e.g. 'Summer Weather Market', 'Peak Winter Heating')")


class SeasonalityEvidence(BaseModel):
    """Day-of-Year historical distribution envelopes and temporal pattern discoveries."""
    day_of_year: int = Field(..., description="Calendar Day of Year (1-366)")
    current_seasonal_z_score: float = Field(..., description="Z-score vs historical day-of-year distribution")
    percentiles_5y: dict[str, float] = Field(default_factory=dict, description="5-year historical percentiles (min, 25%, median, 75%, max)")
    directional_tendency: DirectionalSeasonalTendency | None = Field(default=None, description="Dominant forward directional pattern")
    forward_volatility_expectation: ForwardVolatilityPeak | None = Field(default=None, description="Forward 30-day volatility forecast")


class DivergenceItem(BaseModel):
    """Empirical divergence between two decoupled market signals."""
    type: str = Field(..., description="Divergence classification (e.g. 'PRICE_VS_OI', 'PRICE_VS_COT', 'OUTRIGHT_VS_CURVE')")
    severity: Literal["MILD", "MODERATE", "SEVERE"] = Field(..., description="Statistical divergence intensity")
    description: str = Field(..., description="Objective description of the decoupled variables")


class ProvenanceEvidence(BaseModel):
    """Strict data lineage, lookback parameters, and calculation engine metadata (Section 15)."""
    price_source: str = Field(..., description="Originating price provider / exchange")
    fundamental_source: str | None = Field(default=None, description="Originating agency / report")
    lookback_bars: int = Field(..., description="Number of historical trading bars used in calculation")
    calculation_engine: str = Field(default="QuantEngine_v1.0", description="Engine version")
    generated_at_utc: datetime = Field(..., description="UTC timestamp of evidence package generation")


class QuantitativeEvidencePackage(BaseModel):
    """
    Master Quantitative Evidence Package adhering strictly to Section 5.12.
    Serves as the deterministic foundation supplied to downstream specialized LLM analysts.
    """
    as_of: datetime = Field(..., description="As-of market timestamp")
    market: str = Field(..., description="Canonical commodity ticker (e.g. 'CL', 'BRENT', 'NG', 'ZC')")
    market_state: MarketStateEvidence
    fundamental_state: FundamentalStateEvidence
    positioning_state: COTPositioningEvidence
    spreads: SpreadsEvidence
    cross_commodity: CrossCommodityEvidence
    seasonality: SeasonalityEvidence
    divergences: list[DivergenceItem] = Field(default_factory=list)
    anomalies: list[dict] = Field(default_factory=list)
    contradictions: list[str] = Field(default_factory=list)
    provenance: ProvenanceEvidence
