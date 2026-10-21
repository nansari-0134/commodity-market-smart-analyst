"""
Live Feature Processor & Incremental Rolling Buffer.

Maintains in-memory rolling price, volume, and tick buffers per instrument.
Enables sub-millisecond incremental feature recalculation on incoming ticks
without repeatedly querying database history.
"""
from collections import deque
from datetime import datetime, timezone
from typing import Dict, Optional
import numpy as np

from .config import DEFAULT_FEATURE_CONFIG, FeatureConfig
from .data_quality import QualityStatus
from .schemas import (
    LiveQuantFeaturePackage,
    PriceFeatures,
    TrendFeatures,
    MomentumFeatures,
    VolatilityFeatures,
    VolumeFeatures,
    StructureFeatures,
    VwapFeatures,
    CurveFeatures,
    RelativeValueFeatures,
    OrderFlowFeatures,
    LiquidityFeatures,
    FundamentalsFeatures,
    EventsFeatures,
    RegimeFeatures,
    DivergenceFeatures,
    QuantitativeScores,
)
from .price import calculate_price_features
from .trend import calculate_trend_features
from .momentum import calculate_momentum_features, compute_rsi
from .volatility import calculate_volatility_features
from .location import calculate_location_features
from .volume import calculate_volume_features
from .vwap import calculate_vwap_features
from .market_structure import calculate_market_structure_features
from .support_resistance import calculate_sr_features
from .futures_curve import calculate_curve_features
from .relative_value import calculate_relative_value_features
from .order_flow import calculate_order_flow_features
from .liquidity import calculate_liquidity_features
from .fundamentals import calculate_fundamental_features
from .events import calculate_event_features
from .regime import determine_market_regime
from .divergence import calculate_divergence_features
from .scoring import compute_quantitative_scores


class InstrumentRollingBuffer:
    """In-memory fixed-size rolling buffer for a single instrument."""

    def __init__(self, max_len: int = 252):
        self.prices = deque(maxlen=max_len)
        self.highs = deque(maxlen=max_len)
        self.lows = deque(maxlen=max_len)
        self.volumes = deque(maxlen=max_len)
        self.timestamps = deque(maxlen=max_len)

    def append_bar(self, price: float, high: float, low: float, volume: int, timestamp: Optional[str] = None):
        self.prices.append(price)
        self.highs.append(high)
        self.lows.append(low)
        self.volumes.append(volume)
        self.timestamps.append(timestamp or datetime.now(timezone.utc).isoformat())

    def update_last(self, price: float, high: Optional[float] = None, low: Optional[float] = None, volume: Optional[int] = None):
        """Updates the active live intraday bar in place."""
        if not self.prices:
            self.append_bar(price, high or price, low or price, volume or 0)
            return
        self.prices[-1] = price
        if high is not None:
            self.highs[-1] = max(self.highs[-1], high)
        if low is not None:
            self.lows[-1] = min(self.lows[-1], low)
        if volume is not None:
            self.volumes[-1] = volume


class LiveFeatureProcessor:
    """
    High-frequency live quantitative processor.
    Caches latest calculated feature packages and executes incremental updates.
    """

    def __init__(self, config: Optional[FeatureConfig] = None):
        self.config = config or DEFAULT_FEATURE_CONFIG
        self.buffers: Dict[str, InstrumentRollingBuffer] = {}
        self.cache: Dict[str, LiveQuantFeaturePackage] = {}

    def get_or_create_buffer(self, instrument: str) -> InstrumentRollingBuffer:
        if instrument not in self.buffers:
            self.buffers[instrument] = InstrumentRollingBuffer(max_len=self.config.lookback_annual)
        return self.buffers[instrument]

    def warm_up(self, instrument: str, prices: np.ndarray, highs: np.ndarray, lows: np.ndarray, volumes: np.ndarray):
        """Initializes buffer from historical database bars."""
        buf = self.get_or_create_buffer(instrument)
        for i in range(len(prices)):
            buf.append_bar(
                price=float(prices[i]),
                high=float(highs[i]),
                low=float(lows[i]),
                volume=int(volumes[i]),
            )

    def process_tick(
        self,
        instrument: str,
        name: str,
        sector: str,
        price: float,
        high: Optional[float] = None,
        low: Optional[float] = None,
        volume: Optional[int] = None,
        bid: Optional[float] = None,
        ask: Optional[float] = None,
        timeframe: str = "1D",
    ) -> LiveQuantFeaturePackage:
        """
        Processes a live price tick or bar update and returns the refreshed feature package.
        """
        buf = self.get_or_create_buffer(instrument)
        buf.update_last(price, high, low, volume)

        prices_arr = np.array(buf.prices)
        highs_arr = np.array(buf.highs)
        lows_arr = np.array(buf.lows)
        volumes_arr = np.array(buf.volumes)

        # 1. Price
        price_dict = calculate_price_features(prices_arr, lookback_window=self.config.lookback_short)

        # 2. Trend
        trend_dict = calculate_trend_features(
            prices_arr, highs=highs_arr, lows=lows_arr,
            period_fast=self.config.ema_fast,
            period_medium=self.config.ema_medium,
            period_slow=self.config.ema_slow,
            adx_period=self.config.adx_period,
        )

        # 3. Momentum
        momentum_dict = calculate_momentum_features(
            prices_arr,
            rsi_period=self.config.rsi_period,
            macd_fast=self.config.macd_fast,
            macd_slow=self.config.macd_slow,
            macd_signal=self.config.macd_signal,
        )

        # 4. Volatility
        volatility_dict = calculate_volatility_features(
            prices_arr, highs=highs_arr, lows=lows_arr,
            atr_period=self.config.atr_period,
            realized_vol_window=self.config.realized_vol_period,
        )

        # 5. Volume & VWAP
        volume_dict = calculate_volume_features(volumes_arr, rvol_window=self.config.rvol_window)
        vwap_dict = calculate_vwap_features(prices_arr, volumes_arr, highs=highs_arr, lows=lows_arr)

        # 6. Structure & Range
        structure_base = calculate_market_structure_features(prices_arr, highs=highs_arr, lows=lows_arr, atr=volatility_dict["atr"])
        location_dict = calculate_location_features(prices_arr, highs=highs_arr, lows=lows_arr, vwap=vwap_dict["vwap"])
        sr_dict = calculate_sr_features(prices_arr, highs=highs_arr, lows=lows_arr, atr=volatility_dict["atr"])

        structure_payload = {
            "state": structure_base["state"],
            "range_position_20d": location_dict["range_position_20d"],
            "range_position_60d": location_dict["range_position_60d"],
            "nearest_resistance_distance_pct": sr_dict["nearest_resistance_distance_pct"],
            "nearest_support_distance_pct": sr_dict["nearest_support_distance_pct"],
            "nearest_resistance": sr_dict["nearest_resistance"],
            "nearest_support": sr_dict["nearest_support"],
            "swing_structure": structure_base["swing_structure"],
            "breakout_confirmed": structure_base["breakout_confirmed"],
        }

        # 7. Curve & Relative Value Defaults
        curve_dict = calculate_curve_features([price, price * 0.995, price * 0.99])
        rv_dict = calculate_relative_value_features(prices_arr, None)

        # 8. Liquidity
        liquidity_dict = calculate_liquidity_features(bid=bid, ask=ask)
        order_flow_dict = calculate_order_flow_features(None, None)
        fund_dict = calculate_fundamental_features(None, None, None)
        ev_dict = calculate_event_features(None, None, None)

        # 9. Regime
        regime_dict = determine_market_regime(
            trend_state=trend_dict["trend_state"],
            volatility_regime=volatility_dict["regime"],
            momentum_state=momentum_dict["momentum_state"],
        )

        # 10. Divergence
        rsi_series = compute_rsi(prices_arr, period=self.config.rsi_period)
        divergence_dict = calculate_divergence_features(
            prices=prices_arr,
            rsi_series=rsi_series,
            volumes=volumes_arr,
            timeframe=timeframe,
        )

        # 11. Scores
        scores_dict = compute_quantitative_scores(
            trend_dict=trend_dict,
            momentum_dict=momentum_dict,
            volatility_dict=volatility_dict,
            volume_dict=volume_dict,
            structure_dict=structure_payload,
            curve_dict=curve_dict,
            relative_value_dict=rv_dict,
            fundamentals_dict=fund_dict,
            events_dict=ev_dict,
        )

        package = LiveQuantFeaturePackage(
            instrument=instrument,
            name=name,
            sector=sector,
            timestamp=datetime.now(timezone.utc).isoformat(),
            timeframe=timeframe,
            data_quality=QualityStatus.VALID.value if len(prices_arr) >= 20 else QualityStatus.INSUFFICIENT_HISTORY.value,
            price=PriceFeatures(**price_dict),
            trend=TrendFeatures(**trend_dict),
            momentum=MomentumFeatures(**momentum_dict),
            volatility=VolatilityFeatures(**volatility_dict),
            volume=VolumeFeatures(**volume_dict),
            structure=StructureFeatures(**structure_payload),
            vwap=VwapFeatures(**vwap_dict),
            curve=CurveFeatures(**curve_dict),
            relative_value=RelativeValueFeatures(**rv_dict),
            order_flow=OrderFlowFeatures(**order_flow_dict),
            liquidity=LiquidityFeatures(**liquidity_dict),
            fundamentals=FundamentalsFeatures(**fund_dict),
            events=EventsFeatures(**ev_dict),
            regime=RegimeFeatures(**regime_dict),
            divergence=DivergenceFeatures(**divergence_dict),
            scores=QuantitativeScores(**scores_dict),
        )

        self.cache[instrument] = package
        return package
