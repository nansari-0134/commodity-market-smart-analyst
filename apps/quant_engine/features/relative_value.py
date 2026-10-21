"""
Relative-Value & Cross-Market Analysis Module.

Calculates rolling correlation and relative-value spread/ratio Z-scores
for economically linked benchmark commodity pairs.
"""
from typing import Dict, Optional
import numpy as np
from .data_quality import safe_float, safe_div


def calculate_relative_value_features(
    primary_prices: np.ndarray,
    benchmark_prices: Optional[np.ndarray] = None,
    pair_name: str = "BENCHMARK_PAIR",
    window: int = 60,
) -> Dict:
    """
    Computes rolling correlation and relative-value Z-score against a peer benchmark series.
    """
    if benchmark_prices is None or len(benchmark_prices) < 5 or len(primary_prices) < 5:
        return {
            "benchmark_pair": pair_name,
            "rolling_correlation": 0.0,
            "spread_zscore": 0.0,
        }

    # Align lengths
    min_len = min(len(primary_prices), len(benchmark_prices), window)
    p1 = primary_prices[-min_len:]
    p2 = benchmark_prices[-min_len:]

    # Returns for correlation
    ret1 = np.diff(np.log(np.maximum(p1, 0.001)))
    ret2 = np.diff(np.log(np.maximum(p2, 0.001)))

    if len(ret1) >= 3 and np.std(ret1) > 0 and np.std(ret2) > 0:
        corr_matrix = np.corrcoef(ret1, ret2)
        corr_val = float(corr_matrix[0, 1])
    else:
        corr_val = 0.0

    # Spread series: Price1 / Price2 ratio
    ratios = p1 / np.maximum(p2, 0.001)
    mean_ratio = float(np.mean(ratios))
    std_ratio = float(np.std(ratios, ddof=1)) if len(ratios) > 1 else 0.01

    spread_z = safe_div(float(ratios[-1]) - mean_ratio, std_ratio, default=0.0)

    return {
        "benchmark_pair": pair_name,
        "rolling_correlation": safe_float(corr_val, round_digits=2),
        "spread_zscore": safe_float(spread_z, round_digits=2),
    }
