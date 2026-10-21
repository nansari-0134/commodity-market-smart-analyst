"""
LLM Formatter & Serialization Module.

Formats LiveQuantFeaturePackage into:
1. Compact, machine-readable Section 21 JSON schema.
2. Structured Markdown prompt context for downstream Financial Research LLM ingestion (Phase 13).
"""
import json
from typing import Any, Dict
from .schemas import LiveQuantFeaturePackage


def format_llm_json(package: LiveQuantFeaturePackage, indent: int = 2) -> str:
    """
    Serializes package into the canonical Section 21 JSON representation.
    """
    return package.model_dump_json(indent=indent)


def format_llm_prompt_context(package: LiveQuantFeaturePackage) -> str:
    """
    Converts quantitative features into high-density Markdown text
    designed for financial reasoning LLMs (Gemini, Claude, GPT-4o).
    """
    p = package.price
    t = package.trend
    m = package.momentum
    v = package.volatility
    vol = package.volume
    s = package.structure
    c = package.curve
    f = package.fundamentals
    reg = package.regime
    sc = package.scores

    lines = [
        f"### QUANTITATIVE STATE: {package.name} ({package.instrument})",
        f"- **As of**: {package.timestamp} | **Timeframe**: {package.timeframe} | **Data Quality**: {package.data_quality}",
        f"- **Regime**: {reg.overall.upper()} (Trend: {reg.trend}, Volatility: {reg.volatility})",
        f"- **Composite Score**: {sc.overall_composite_score:+.2f} [-1.0 Bearish to +1.0 Bullish]",
        "",
        "#### 1. Price & Multi-Horizon Returns",
        f"- Last Price: ${p.last:.2f} | 1D Return: {p.return_1d:+.2%} (Log: {p.log_return_1d:+.4f})",
        f"- 20D Percentile Rank: {p.percentile_20d:.1f}% | 20D Z-Score: {p.zscore_20d:+.2f}σ",
        f"- Acceleration: {p.return_acceleration_1d:+.4f}",
        "",
        "#### 2. Trend & Momentum",
        f"- Trend Structure: {t.ema_structure.upper()} (EMA Slope: {t.ema_slope}) | ADX(14): {t.adx:.1f} ({t.trend_state})",
        f"- Distance to EMAs: 20-EMA: {t.dist_ema20_pct:+.2f}% | 50-EMA: {t.dist_ema50_pct:+.2f}% | 200-EMA: {t.dist_ema200_pct:+.2f}%",
        f"- RSI(14): {m.rsi:.1f} (Percentile: {m.rsi_percentile:.1f}%, Direction: {m.rsi_direction})",
        f"- MACD Histogram: {m.macd_histogram:+.3f} ({m.histogram_direction}) | State: {m.momentum_state.upper()}",
        "",
        "#### 3. Volatility, Volume & Location",
        f"- ATR(14): ${v.atr:.2f} ({v.atr_pct:.2f}% of price) | Percentile: {v.atr_percentile:.1f}%",
        f"- Realized Vol (20D Ann): {v.realized_volatility:.1f}% (Percentile: {v.vol_percentile:.1f}%, Regime: {v.regime.upper()})",
        f"- Volume: {vol.volume:,} | RVOL: {vol.relative_volume:.2f}x (Z-Score: {vol.zscore:+.2f}σ, State: {vol.state.upper()})",
        f"- Range Position: 20D: {s.range_position_20d:.1f}% | 60D: {s.range_position_60d:.1f}%",
        f"- Structural Levels: Res: ${s.nearest_resistance:.2f} ({s.nearest_resistance_distance_pct:+.2f}%) | Sup: ${s.nearest_support:.2f} ({s.nearest_support_distance_pct:+.2f}%)",
        f"- Market Structure: {s.swing_structure.upper()} ({s.state.upper()})",
        "",
        "#### 4. Futures Curve & Fundamentals",
        f"- Term Structure: {c.curve_state.upper()} | F1-F2 Spread: ${c.spread_f1_f2:+.3f} (Z: {c.spread_zscore:+.2f}σ, Pct: {c.spread_percentile:.1f}%)",
        f"- Annualized Curve Slope: {c.curve_slope_annualized:+.2%}",
    ]

    if f.primary_variable:
        lines.append(
            f"- Fundamental ({f.primary_variable}): {f.latest_value} vs 5Y Normal {f.normal_reference} "
            f"(Dev: {f.deviation_pct:+.1f}%, Z: {f.inventory_zscore:+.2f}σ, Momentum: {f.fundamental_momentum.upper()})"
        )

    if package.divergence.has_divergence:
        lines.append("")
        lines.append("#### 5. Active Divergences")
        for div in package.divergence.active_divergences:
            lines.append(f"- **{div.divergence_type.upper()}**: {div.direction.upper()} ({div.severity.upper()}) — {div.description}")

    lines.append("")
    lines.append("#### 6. Multi-Factor Quant Ratings [-1.0 to +1.0]")
    lines.append(
        f"Trend: {sc.trend_score:+.2f} | Momentum: {sc.momentum_score:+.2f} | Volatility: {sc.volatility_score:.2f} | "
        f"Volume: {sc.volume_score:.2f} | Structure: {sc.structure_score:+.2f} | Curve: {sc.curve_score:+.2f} | "
        f"Fundamentals: {sc.fundamentals_score:+.2f}"
    )

    return "\n".join(lines)
