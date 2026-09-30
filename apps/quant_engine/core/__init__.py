"""
Zero-ORM Vectorized Calculation Core Package.
"""
from apps.quant_engine.core.market_state import (
    compute_returns,
    compute_realized_volatility,
    compute_garman_klass_volatility,
    compute_atr,
    compute_volume_metrics,
    classify_oi_regime,
)
from apps.quant_engine.core.spline import (
    fit_forward_curve_spline,
    sample_forward_curve,
)
from apps.quant_engine.core.curve import (
    analyze_curve_structure,
)
from apps.quant_engine.core.spreads import (
    compute_321_crack_spread,
    compute_soybean_crush_spread,
    compute_spark_spread,
)
from apps.quant_engine.core.cross_commodity import (
    LOGICAL_COMMODITY_COMPLEXES,
    find_logical_complex_for_commodity,
    compute_all_pairs_correlation_matrix,
    run_engle_granger_cointegration,
    compute_macro_factor_sensitivities,
)
from apps.quant_engine.core.seasonality import (
    compute_seasonal_envelopes,
    find_directional_tenure_patterns,
    compute_forward_volatility_expectation,
    compute_comprehensive_seasonality_profile,
    COMMODITY_CALENDAR_CYCLES,
)
from apps.quant_engine.core.divergence import (
    compute_mad_zscore,
    detect_price_oi_divergence,
    detect_price_cot_divergence,
    detect_price_curve_divergence,
)

__all__ = [
    "compute_returns",
    "compute_realized_volatility",
    "compute_garman_klass_volatility",
    "compute_atr",
    "compute_volume_metrics",
    "classify_oi_regime",
    "fit_forward_curve_spline",
    "sample_forward_curve",
    "analyze_curve_structure",
    "compute_321_crack_spread",
    "compute_soybean_crush_spread",
    "compute_spark_spread",
    "LOGICAL_COMMODITY_COMPLEXES",
    "find_logical_complex_for_commodity",
    "compute_all_pairs_correlation_matrix",
    "run_engle_granger_cointegration",
    "compute_macro_factor_sensitivities",
    "compute_seasonal_envelopes",
    "find_directional_tenure_patterns",
    "compute_forward_volatility_expectation",
    "compute_comprehensive_seasonality_profile",
    "COMMODITY_CALENDAR_CYCLES",
    "compute_mad_zscore",
    "detect_price_oi_divergence",
    "detect_price_cot_divergence",
    "detect_price_curve_divergence",
]
