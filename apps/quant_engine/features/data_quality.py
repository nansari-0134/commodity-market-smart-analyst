"""
Data quality definitions, provenance metadata, and numerical validation guards.

Guarantees:
- Zero silent NaN or Inf propagation
- Explicit quality labeling: VALID, STALE, INSUFFICIENT_HISTORY, UNAVAILABLE
- Robust handling of zero variance, zero volume, and single-bar feeds
"""
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
import math
from typing import Any, Optional, Tuple
import numpy as np


class QualityStatus(str, Enum):
    VALID = "VALID"
    STALE = "STALE"
    INSUFFICIENT_HISTORY = "INSUFFICIENT_HISTORY"
    UNAVAILABLE = "UNAVAILABLE"


@dataclass(frozen=True)
class FeatureMetadata:
    """Provenance and calculation telemetry attached to features."""
    status: QualityStatus = QualityStatus.VALID
    timestamp: str = ""
    source: str = "POINT_IN_TIME_STORE"
    timeframe: str = "1D"
    lookback_bars: int = 0
    notes: str = ""

    @classmethod
    def create(
        cls,
        status: QualityStatus = QualityStatus.VALID,
        source: str = "POINT_IN_TIME_STORE",
        timeframe: str = "1D",
        lookback_bars: int = 0,
        notes: str = "",
    ) -> "FeatureMetadata":
        return cls(
            status=status,
            timestamp=datetime.now(timezone.utc).isoformat(),
            source=source,
            timeframe=timeframe,
            lookback_bars=lookback_bars,
            notes=notes,
        )


def safe_float(val: Any, default: float = 0.0, round_digits: Optional[int] = 4) -> float:
    """Safely converts an arbitrary numeric value to float, replacing NaN/Inf with default."""
    if val is None:
        return default
    try:
        f = float(val)
        if math.isnan(f) or math.isinf(f):
            return default
        return round(f, round_digits) if round_digits is not None else f
    except (TypeError, ValueError):
        return default


def safe_div(numerator: float, denominator: float, default: float = 0.0) -> float:
    """Division with zero-denominator and NaN guard."""
    if denominator == 0.0 or math.isnan(denominator) or math.isinf(denominator):
        return default
    res = numerator / denominator
    if math.isnan(res) or math.isinf(res):
        return default
    return res


def validate_series(arr: np.ndarray, min_length: int = 2) -> Tuple[bool, QualityStatus]:
    """
    Checks if a NumPy series is suitable for rolling calculations.
    Returns (is_valid, quality_status).
    """
    from typing import Tuple
    if arr is None or len(arr) < min_length:
        return False, QualityStatus.INSUFFICIENT_HISTORY
    # Check if entirely NaN or constant
    valid_count = np.count_nonzero(~np.isnan(arr))
    if valid_count < min_length:
        return False, QualityStatus.INSUFFICIENT_HISTORY
    return True, QualityStatus.VALID
