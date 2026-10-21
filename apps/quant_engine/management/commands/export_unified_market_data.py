"""
Management command to export a unified, multi-asset, cross-domain institutional Excel workbook.

Merges:
1. All Products / Physical Commodities (CommodityMaster)
2. All Contracts / Tenors (MarketPriceObservation prompt + forward curve strips M1-M24)
3. OHLCV, volume, and open interest
4. Quant Engine analytics (Returns, EMAs, RSI, MACD, ATR, Vol, Z-scores, Regimes, Composite Scores)
5. Physical Supply / Demand fundamentals (EIA inventories, Cushing storage, USDA WASDE balances)
6. CFTC Commitment of Traders (Managed Money Net, Commercial Net, Spec % OI)
7. News Intelligence (Wire headlines, sentiment scores, publisher desks, tags)
8. Catalyst Reports (OPEC, WASDE, FOMC, EIA releases, consensus, actual, surprise delta)
9. Complete Data Dictionary & Metadata Methodology
"""

import os
from datetime import date, datetime
from decimal import Decimal
import numpy as np
import pandas as pd
from django.core.management.base import BaseCommand
from django.db.models import Prefetch

import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

from apps.commodities.models import CommodityMaster
from apps.market_data.models import (
    MarketPriceObservation,
    FundamentalObservation,
    CommitmentOfTradersObservation,
)
from apps.news_intel.models import (
    NewsArticle,
    MarketCatalystEvent,
)


class Command(BaseCommand):
    help = "Export unified Excel workbook merging Products, Contracts, OHLCV, Quant Engine, Fundamentals, News, and Reports."

    def add_arguments(self, parser):
        parser.add_argument(
            "--output",
            type=str,
            default="Commodity_Market_Intelligence_Master_Dataset.xlsx",
            help="Destination filepath for the generated Excel workbook (default: Commodity_Market_Intelligence_Master_Dataset.xlsx)",
        )
        parser.add_argument(
            "--start-date",
            type=str,
            default="2024-01-01",
            help="Start date for the unified master time series (YYYY-MM-DD, default: 2024-01-01 for high-density multi-year analysis)",
        )
        parser.add_argument(
            "--all-history",
            action="store_true",
            help="Export full 20+ year price observation history across all sheets",
        )

    def handle(self, *args, **options):
        output_path = options["output"]
        start_date_str = options["start_date"]
        all_history = options["all_history"]

        self.stdout.write(self.style.SUCCESS("Starting Unified Commodity Market Intelligence Excel Export..."))

        # -------------------------------------------------------------
        # 1. Fetch Reference Metadata: Commodities & Units
        # -------------------------------------------------------------
        self.stdout.write("  -> Loading commodity master and listings...")
        commodities = {
            c.code: {
                "name": c.name,
                "sector": c.sector,
                "exchange": c.primary_exchange.code if c.primary_exchange else "CME",
                "unit": c.pricing_unit.symbol if c.pricing_unit else "$",
            }
            for c in CommodityMaster.objects.select_related("primary_exchange", "pricing_unit").all()
        }

        # -------------------------------------------------------------
        # 2. Build Daily News Intelligence Lookup
        # -------------------------------------------------------------
        self.stdout.write("  -> Mapping news articles and sentiment by commodity and date...")
        news_map = {}  # (date, commodity_code) -> list of articles
        news_articles_qs = NewsArticle.objects.prefetch_related("commodity_tags__commodity").all()
        news_rows_for_sheet = []

        for article in news_articles_qs:
            art_date = article.published_at_utc.date()
            tagged_codes = [tag.commodity.code for tag in article.commodity_tags.all()]
            news_rows_for_sheet.append({
                "published_date": art_date,
                "published_time_utc": article.published_at_utc.strftime("%Y-%m-%d %H:%M:%S"),
                "source_name": article.source_name,
                "author": article.author or "Staff Desk",
                "title": article.title,
                "summary": article.summary,
                "sentiment_score": float(article.overall_sentiment_score),
                "sentiment_label": article.overall_sentiment_label,
                "linked_commodities": ", ".join(tagged_codes) if tagged_codes else "MACRO",
                "source_url": article.source_url or "https://terminal.market-intelligence.internal",
            })
            for c_code in tagged_codes:
                key = (art_date, c_code)
                if key not in news_map:
                    news_map[key] = []
                news_map[key].append(article)

        # -------------------------------------------------------------
        # 3. Build Daily Catalyst Reports Lookup
        # -------------------------------------------------------------
        self.stdout.write("  -> Mapping catalyst events and releases by commodity and date...")
        catalyst_map = {}  # (date, commodity_code) -> list of events
        catalyst_events_qs = MarketCatalystEvent.objects.select_related("primary_commodity", "unit").prefetch_related("affected_commodities").all()
        catalyst_rows_for_sheet = []

        for evt in catalyst_events_qs:
            evt_date = evt.scheduled_datetime_utc.date()
            aff_codes = [c.code for c in evt.affected_commodities.all()]
            prim_code = evt.primary_commodity.code if evt.primary_commodity else None
            all_target_codes = set(aff_codes)
            if prim_code:
                all_target_codes.add(prim_code)

            surprise_val = float(evt.surprise_magnitude) if evt.surprise_magnitude is not None else None

            catalyst_rows_for_sheet.append({
                "scheduled_date": evt_date,
                "scheduled_time_utc": evt.scheduled_datetime_utc.strftime("%Y-%m-%d %H:%M:%S"),
                "event_name": evt.name,
                "event_type": evt.event_type,
                "source_agency": evt.source_agency,
                "impact_level": evt.impact_level,
                "status": evt.status,
                "primary_commodity": prim_code or "MACRO",
                "affected_commodities": ", ".join(aff_codes) if aff_codes else "BROAD_SECTOR",
                "period_covered": evt.period_covered,
                "consensus_expectation": float(evt.consensus_expectation) if evt.consensus_expectation is not None else None,
                "actual_value": float(evt.actual_value) if evt.actual_value is not None else None,
                "prior_value": float(evt.prior_value) if evt.prior_value is not None else None,
                "surprise_magnitude": surprise_val,
                "surprise_direction": evt.surprise_direction,
                "unit": evt.unit.symbol if evt.unit else "",
                "notes": evt.notes,
            })

            for code in all_target_codes:
                k = (evt_date, code)
                if k not in catalyst_map:
                    catalyst_map[k] = []
                catalyst_map[k].append(evt)

        # -------------------------------------------------------------
        # 4. Build Supply / Demand Fundamentals Lookup
        # -------------------------------------------------------------
        self.stdout.write("  -> Mapping physical fundamentals & COT positioning...")
        fund_map = {}  # (date, commodity_code) -> list of fundamentals
        fund_obs_qs = FundamentalObservation.objects.select_related("variable", "variable__commodity", "unit").all()
        fund_rows_for_sheet = []

        for f in fund_obs_qs:
            c_code = f.variable.commodity.code if (f.variable and f.variable.commodity) else "MACRO"
            val_float = float(f.value) if f.value is not None else None
            unit_sym = f.unit.symbol if f.unit else ""
            fund_rows_for_sheet.append({
                "observation_date": f.observation_date,
                "commodity_code": c_code,
                "variable_code": f.variable.code if f.variable else "VAR",
                "variable_name": f.variable.name if f.variable else "",
                "data_type": f.variable.data_type if f.variable else "",
                "period_start": f.period_start,
                "period_end": f.period_end,
                "observed_value": val_float,
                "unit": unit_sym,
                "quality_status": f.quality_status,
            })
            key = (f.observation_date, c_code)
            if key not in fund_map:
                fund_map[key] = []
            fund_map[key].append(f)

        # Build COT Lookup
        cot_map = {}  # (date, commodity_code) -> COT record
        cot_obs_qs = CommitmentOfTradersObservation.objects.select_related("commodity").all()
        cot_rows_for_sheet = []

        for cot in cot_obs_qs:
            c_code = cot.commodity.code if cot.commodity else "GENERIC"
            net_mm = cot.money_manager_net
            net_comm = cot.commercial_net
            pct_oi = cot.money_manager_net_pct_oi

            row = {
                "observation_date": cot.observation_date,
                "commodity_code": c_code,
                "open_interest": cot.open_interest,
                "managed_money_long": cot.money_manager_long,
                "managed_money_short": cot.money_manager_short,
                "managed_money_net": net_mm,
                "commercial_long": (cot.prod_merc_long or 0) + (cot.swap_long or 0),
                "commercial_short": (cot.prod_merc_short or 0) + (cot.swap_short or 0),
                "commercial_net": net_comm,
                "managed_money_net_pct_oi": pct_oi,
            }
            cot_rows_for_sheet.append(row)
            cot_map[(cot.observation_date, c_code)] = row

        # -------------------------------------------------------------
        # 5. Extract Price Observations & Vectorize Quant Features
        # -------------------------------------------------------------
        self.stdout.write("  -> Loading and calculating quantitative features across price bars...")
        price_filter = {}
        if not all_history and start_date_str:
            cutoff = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            # For accurate EMA/Vol rolling calculation, load from 200 bars prior or full dataset
            # We compute features on all prompt bars per commodity, then filter for master sheet
        
        # Load all prompt price observations grouped by commodity
        raw_prices = list(
            MarketPriceObservation.objects.select_related("commodity")
            .order_by("commodity__code", "observation_date")
            .values(
                "commodity__code",
                "observation_date",
                "delivery_month",
                "is_prompt",
                "open_price",
                "high_price",
                "low_price",
                "close_price",
                "settlement_price",
                "volume",
                "open_interest",
            )
        )

        all_prices_df = pd.DataFrame(raw_prices)
        if all_prices_df.empty:
            self.stdout.write(self.style.ERROR("No market price observations found in database!"))
            return

        all_prices_df["close_clean"] = all_prices_df["close_price"].fillna(all_prices_df["settlement_price"]).astype(float)
        all_prices_df["open_clean"] = all_prices_df["open_price"].fillna(all_prices_df["close_clean"]).astype(float)
        all_prices_df["high_clean"] = all_prices_df["high_price"].fillna(all_prices_df["close_clean"]).astype(float)
        all_prices_df["low_clean"] = all_prices_df["low_price"].fillna(all_prices_df["close_clean"]).astype(float)
        all_prices_df["vol_clean"] = all_prices_df["volume"].fillna(0).astype(float)
        all_prices_df["oi_clean"] = all_prices_df["open_interest"].fillna(0).astype(float)

        # -------------------------------------------------------------
        # 6. Compute Point-in-Time Quantitative Features (Prompt Series)
        # -------------------------------------------------------------
        prompt_df = all_prices_df[all_prices_df["is_prompt"] == True].copy()
        quant_features_list = []

        for code, group in prompt_df.groupby("commodity__code"):
            grp = group.sort_values("observation_date").copy()
            p = grp["close_clean"]
            h = grp["high_clean"]
            l = grp["low_clean"]
            v = grp["vol_clean"]

            # Multi-Horizon Returns & Log Returns
            grp["ret_1d"] = p.pct_change()
            grp["log_ret_1d"] = np.log(p / p.shift(1))
            grp["ret_5d"] = p.pct_change(5)
            grp["ret_20d"] = p.pct_change(20)
            grp["ret_accel_1d"] = grp["ret_1d"].diff()

            # Statistical Normalization
            roll20_mean = p.rolling(20).mean()
            roll20_std = p.rolling(20).std().replace(0, np.nan)
            grp["zscore_20d"] = (p - roll20_mean) / roll20_std
            grp["percentile_20d"] = p.rolling(20).apply(
                lambda s: (s <= s.iloc[-1]).mean() * 100.0 if len(s) > 0 and not np.isnan(s.iloc[-1]) else 50.0,
                raw=False,
            )

            roll60_mean = p.rolling(60).mean()
            roll60_std = p.rolling(60).std().replace(0, np.nan)
            grp["zscore_60d"] = (p - roll60_mean) / roll60_std

            # Triple EMAs
            grp["ema_20"] = p.ewm(span=20, adjust=False).mean()
            grp["ema_50"] = p.ewm(span=50, adjust=False).mean()
            grp["ema_200"] = p.ewm(span=200, adjust=False).mean()
            grp["dist_ema_20_pct"] = ((p - grp["ema_20"]) / grp["ema_20"]) * 100.0
            grp["dist_ema_50_pct"] = ((p - grp["ema_50"]) / grp["ema_50"]) * 100.0
            grp["dist_ema_200_pct"] = ((p - grp["ema_200"]) / grp["ema_200"]) * 100.0

            # Trend Classification
            def classify_trend(row):
                if row["close_clean"] >= row["ema_20"] > row["ema_50"] > row["ema_200"]:
                    return "bullish"
                elif row["close_clean"] <= row["ema_20"] < row["ema_50"] < row["ema_200"]:
                    return "bearish"
                return "neutral"
            grp["trend_regime"] = grp.apply(classify_trend, axis=1)

            # Wilder's 14-period RSI
            delta = p.diff()
            gain = delta.where(delta > 0, 0.0).ewm(alpha=1/14, adjust=False).mean()
            loss = (-delta.where(delta < 0, 0.0)).ewm(alpha=1/14, adjust=False).mean()
            rs = gain / loss.replace(0, np.nan)
            grp["rsi_14"] = 100.0 - (100.0 / (1.0 + rs))
            grp["rsi_percentile_60d"] = grp["rsi_14"].rolling(60).apply(
                lambda s: (s <= s.iloc[-1]).mean() * 100.0 if len(s) > 0 and not np.isnan(s.iloc[-1]) else 50.0,
                raw=False,
            )

            # MACD (12, 26, 9)
            ema12 = p.ewm(span=12, adjust=False).mean()
            ema26 = p.ewm(span=26, adjust=False).mean()
            grp["macd_line"] = ema12 - ema26
            grp["macd_signal"] = grp["macd_line"].ewm(span=9, adjust=False).mean()
            grp["macd_hist"] = grp["macd_line"] - grp["macd_signal"]

            # ATR(14)
            tr1 = h - l
            tr2 = (h - p.shift(1)).abs()
            tr3 = (l - p.shift(1)).abs()
            tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
            grp["atr_14"] = tr.ewm(alpha=1/14, adjust=False).mean()
            grp["atr_pct_of_price"] = (grp["atr_14"] / p) * 100.0

            # Realized Volatility 20D Annualized
            grp["realized_vol_20d_pct"] = grp["log_ret_1d"].rolling(20).std() * np.sqrt(252) * 100.0

            # Volatility Regime
            def classify_vol(vol):
                if np.isnan(vol): return "normal"
                if vol < 15.0: return "low"
                if vol < 30.0: return "normal"
                if vol < 50.0: return "high"
                return "extreme"
            grp["vol_regime"] = grp["realized_vol_20d_pct"].apply(classify_vol)

            # High-Low Range Position (20D, 60D)
            low20 = l.rolling(20).min()
            high20 = h.rolling(20).max()
            grp["range_pos_20d_pct"] = ((p - low20) / (high20 - low20).replace(0, np.nan)) * 100.0

            low60 = l.rolling(60).min()
            high60 = h.rolling(60).max()
            grp["range_pos_60d_pct"] = ((p - low60) / (high60 - low60).replace(0, np.nan)) * 100.0

            # Relative Volume (RVOL 20D)
            vol20 = v.rolling(20).mean().replace(0, np.nan)
            grp["rvol_20d"] = v / vol20
            vol_std = v.rolling(20).std().replace(0, np.nan)
            grp["volume_zscore_20d"] = (v - vol20) / vol_std

            # Composite Market Regime
            grp["composite_market_regime"] = grp["trend_regime"] + "_" + grp["vol_regime"] + "_volatility"

            # Composite Quant Score (-1.0 to +1.0)
            def compute_quant_score(row):
                t_score = 1.0 if row["trend_regime"] == "bullish" else (-1.0 if row["trend_regime"] == "bearish" else 0.0)
                m_score = ((row["rsi_14"] - 50.0) / 50.0) if not np.isnan(row["rsi_14"]) else 0.0
                v_score = -0.5 if row["vol_regime"] == "extreme" else (0.2 if row["vol_regime"] == "normal" else 0.0)
                score = round(t_score * 0.45 + m_score * 0.35 + v_score * 0.20, 3)
                return max(-1.0, min(1.0, score))
            grp["composite_quant_score"] = grp.apply(compute_quant_score, axis=1)

            quant_features_list.append(grp)

        quant_df = pd.concat(quant_features_list, ignore_index=True)
        quant_lookup = {
            (row["observation_date"], row["commodity__code"]): row
            for _, row in quant_df.iterrows()
        }

        # -------------------------------------------------------------
        # 7. Assemble Unified Master Sheet Data
        # -------------------------------------------------------------
        self.stdout.write("  -> Assembling Unified Master dataset rows...")
        cutoff_date = datetime.strptime(start_date_str, "%Y-%m-%d").date() if not all_history else date(2000, 1, 1)

        master_rows = []
        for _, qrow in quant_df.iterrows():
            obs_date = qrow["observation_date"]
            if obs_date < cutoff_date:
                continue

            c_code = qrow["commodity__code"]
            c_meta = commodities.get(c_code, {"name": c_code, "sector": "COMMODITIES", "exchange": "EXCH", "unit": "$"})

            # Physical fundamentals for that date
            funds = fund_map.get((obs_date, c_code), [])
            prim_fund = funds[0] if funds else None
            fund_metric = prim_fund.variable.name if (prim_fund and prim_fund.variable) else None
            fund_val = float(prim_fund.value) if (prim_fund and prim_fund.value is not None) else None
            fund_unit = prim_fund.unit.symbol if (prim_fund and prim_fund.unit) else None

            # COT positioning
            cot_rec = cot_map.get((obs_date, c_code))
            cot_mm_net = cot_rec["managed_money_net"] if cot_rec else None
            cot_comm_net = cot_rec["commercial_net"] if cot_rec else None
            cot_pct_oi = cot_rec["managed_money_net_pct_oi"] if cot_rec else None

            # News articles on that date
            news_list = news_map.get((obs_date, c_code), [])
            top_news = news_list[0] if news_list else None
            news_count = len(news_list)
            news_headline = top_news.title if top_news else None
            news_sentiment = float(top_news.overall_sentiment_score) if top_news else None
            news_sentiment_label = top_news.overall_sentiment_label if top_news else None
            news_source = top_news.source_name if top_news else None

            # Catalyst reports on that date
            cat_list = catalyst_map.get((obs_date, c_code), [])
            top_cat = cat_list[0] if cat_list else None
            cat_count = len(cat_list)
            cat_name = top_cat.name if top_cat else None
            cat_agency = top_cat.source_agency if top_cat else None
            cat_impact = top_cat.impact_level if top_cat else None
            cat_consensus = float(top_cat.consensus_expectation) if (top_cat and top_cat.consensus_expectation is not None) else None
            cat_actual = float(top_cat.actual_value) if (top_cat and top_cat.actual_value is not None) else None
            cat_surprise = float(top_cat.surprise_magnitude) if (top_cat and top_cat.surprise_magnitude is not None) else None
            cat_surprise_dir = top_cat.surprise_direction if top_cat else None

            # Round quant values safely
            def r(val, digits=4):
                if pd.isna(val) or val is None:
                    return None
                return round(float(val), digits)

            master_rows.append({
                "Date": obs_date,
                "Commodity_Code": c_code,
                "Commodity_Name": c_meta["name"],
                "Sector": c_meta["sector"],
                "Exchange": c_meta["exchange"],
                "Delivery_Month": qrow["delivery_month"] or "PROMPT",
                "Is_Prompt": "YES" if qrow["is_prompt"] else "NO",
                "Pricing_Unit": c_meta["unit"],
                "Open": r(qrow["open_clean"], 4),
                "High": r(qrow["high_clean"], 4),
                "Low": r(qrow["low_clean"], 4),
                "Close": r(qrow["close_clean"], 4),
                "Volume": int(qrow["vol_clean"]),
                "Open_Interest": int(qrow["oi_clean"]),
                "Return_1D_Pct": r(qrow["ret_1d"] * 100.0 if not pd.isna(qrow["ret_1d"]) else None, 2),
                "Log_Return_1D": r(qrow["log_ret_1d"], 4),
                "Return_5D_Pct": r(qrow["ret_5d"] * 100.0 if not pd.isna(qrow["ret_5d"]) else None, 2),
                "Return_20D_Pct": r(qrow["ret_20d"] * 100.0 if not pd.isna(qrow["ret_20d"]) else None, 2),
                "Return_Accel_1D": r(qrow["ret_accel_1d"] * 100.0 if not pd.isna(qrow["ret_accel_1d"]) else None, 2),
                "Price_Percentile_20D": r(qrow["percentile_20d"], 1),
                "Price_ZScore_20D": r(qrow["zscore_20d"], 2),
                "EMA_20": r(qrow["ema_20"], 2),
                "EMA_50": r(qrow["ema_50"], 2),
                "EMA_200": r(qrow["ema_200"], 2),
                "Dist_EMA_20_Pct": r(qrow["dist_ema_20_pct"], 2),
                "Dist_EMA_50_Pct": r(qrow["dist_ema_50_pct"], 2),
                "Dist_EMA_200_Pct": r(qrow["dist_ema_200_pct"], 2),
                "Trend_Regime": qrow["trend_regime"],
                "RSI_14": r(qrow["rsi_14"], 2),
                "RSI_Percentile_60D": r(qrow["rsi_percentile_60d"], 1),
                "MACD_Line": r(qrow["macd_line"], 3),
                "MACD_Signal": r(qrow["macd_signal"], 3),
                "MACD_Hist": r(qrow["macd_hist"], 3),
                "ATR_14": r(qrow["atr_14"], 2),
                "ATR_Pct_Of_Price": r(qrow["atr_pct_of_price"], 2),
                "Realized_Vol_20D_Pct": r(qrow["realized_vol_20d_pct"], 2),
                "Volatility_Regime": qrow["vol_regime"],
                "Range_Pos_20D_Pct": r(qrow["range_pos_20d_pct"], 1),
                "Range_Pos_60D_Pct": r(qrow["range_pos_60d_pct"], 1),
                "RVOL_20D": r(qrow["rvol_20d"], 2),
                "Volume_ZScore_20D": r(qrow["volume_zscore_20d"], 2),
                "Composite_Market_Regime": qrow["composite_market_regime"],
                "Composite_Quant_Score": r(qrow["composite_quant_score"], 3),
                "Physical_Inventory_Metric": fund_metric or "N/A",
                "Physical_Inventory_Value": fund_val,
                "Physical_Inventory_Unit": fund_unit or "",
                "COT_Managed_Money_Net": cot_mm_net,
                "COT_Commercial_Net": cot_comm_net,
                "COT_Managed_Money_Net_Pct_OI": cot_pct_oi,
                "News_Articles_Count": news_count,
                "Top_News_Headline": news_headline or "No published wire updates",
                "News_Sentiment_Score": news_sentiment,
                "News_Sentiment_Label": news_sentiment_label or "NEUTRAL",
                "News_Source_Desk": news_source or "",
                "Catalyst_Reports_Count": cat_count,
                "Top_Catalyst_Report": cat_name or "No scheduled release",
                "Catalyst_Agency": cat_agency or "",
                "Catalyst_Impact_Level": cat_impact or "",
                "Catalyst_Consensus": cat_consensus,
                "Catalyst_Actual": cat_actual,
                "Catalyst_Surprise_Delta": cat_surprise,
                "Catalyst_Surprise_Direction": cat_surprise_dir or "IN_LINE",
            })

        master_df = pd.DataFrame(master_rows)

        # -------------------------------------------------------------
        # 8. Build All Contracts & Tenor Strip DataFrame
        # -------------------------------------------------------------
        self.stdout.write("  -> Assembling full All-Contracts OHLCV rows...")
        all_contracts_rows = []
        for _, r in all_prices_df.iterrows():
            c_code = r["commodity__code"]
            c_meta = commodities.get(c_code, {"name": c_code, "sector": "COMMODITIES", "exchange": "EXCH", "unit": "$"})
            all_contracts_rows.append({
                "Date": r["observation_date"],
                "Commodity_Code": c_code,
                "Commodity_Name": c_meta["name"],
                "Sector": c_meta["sector"],
                "Exchange": c_meta["exchange"],
                "Delivery_Month": r["delivery_month"] or ("PROMPT" if r["is_prompt"] else "BAR"),
                "Is_Prompt": "YES" if r["is_prompt"] else "NO",
                "Open": round(r["open_clean"], 4) if pd.notna(r["open_clean"]) else None,
                "High": round(r["high_clean"], 4) if pd.notna(r["high_clean"]) else None,
                "Low": round(r["low_clean"], 4) if pd.notna(r["low_clean"]) else None,
                "Close": round(r["close_clean"], 4) if pd.notna(r["close_clean"]) else None,
                "Settlement": round(float(r["settlement_price"]), 4) if pd.notna(r["settlement_price"]) else round(r["close_clean"], 4),
                "Volume": int(r["vol_clean"]),
                "Open_Interest": int(r["oi_clean"]),
                "Pricing_Unit": c_meta["unit"],
            })
        all_contracts_df = pd.DataFrame(all_contracts_rows)

        # -------------------------------------------------------------
        # 9. Build Data Dictionary & Metadata Methodology DataFrame
        # -------------------------------------------------------------
        dict_rows = [
            ("Unified_Master_Dataset", "Date", "Date (YYYY-MM-DD)", "Pricing / session observation date", "Official exchange daily close"),
            ("Unified_Master_Dataset", "Commodity_Code", "String", "Canonical commodity derivative code", "CommodityMaster identifier"),
            ("Unified_Master_Dataset", "Commodity_Name", "String", "Full institutional asset name", "CommodityMaster name"),
            ("Unified_Master_Dataset", "Sector", "String", "Asset class classification (ENERGY, METALS_PRECIOUS, GRAINS, etc.)", "CommodityMaster sector"),
            ("Unified_Master_Dataset", "Exchange", "String", "Primary benchmark derivative venue", "ExchangeMaster venue code"),
            ("Unified_Master_Dataset", "Delivery_Month", "String", "Contract delivery tenor or PROMPT continuous", "Contract specification"),
            ("Unified_Master_Dataset", "Is_Prompt", "Boolean Flag", "True/YES if continuous front-month benchmark contract", "Point-in-Time benchmark roll"),
            ("Unified_Master_Dataset", "Open", "Float / Currency", "Session opening price", "Exchange bar opening tick"),
            ("Unified_Master_Dataset", "High", "Float / Currency", "Session maximum price", "Exchange bar high"),
            ("Unified_Master_Dataset", "Low", "Float / Currency", "Session minimum price", "Exchange bar low"),
            ("Unified_Master_Dataset", "Close", "Float / Currency", "Session closing / preliminary settlement price", "Official session close"),
            ("Unified_Master_Dataset", "Volume", "Integer", "Total derivative contracts traded during session", "Exchange clearing volume"),
            ("Unified_Master_Dataset", "Open_Interest", "Integer", "Total open derivative contracts outstanding at close", "Exchange / COT clearing settlement"),
            ("Unified_Master_Dataset", "Return_1D_Pct", "Percentage (%)", "1-day percentage return: (P_t - P_t-1) / P_t-1 * 100", "Quant Engine price module"),
            ("Unified_Master_Dataset", "Log_Return_1D", "Float", "Continuous compounding log return: ln(P_t / P_t-1)", "Quant Engine mathematical normalization"),
            ("Unified_Master_Dataset", "Return_5D_Pct", "Percentage (%)", "5-trading-day cumulative percentage return", "Quant Engine momentum module"),
            ("Unified_Master_Dataset", "Return_20D_Pct", "Percentage (%)", "20-trading-day (1 calendar month) cumulative return", "Quant Engine momentum module"),
            ("Unified_Master_Dataset", "Return_Accel_1D", "Percentage (%)", "Return acceleration: Ret_1D_t - Ret_1D_t-1", "Quant Engine 2nd derivative dynamics"),
            ("Unified_Master_Dataset", "Price_Percentile_20D", "Percentile (0-100)", "Empirical percentile rank of price vs 20-day distribution", "Quant Engine statistics module"),
            ("Unified_Master_Dataset", "Price_ZScore_20D", "Float (Z-Score)", "Normalized Z-Score: (P - Mean20) / Std20", "Quant Engine statistical normalization"),
            ("Unified_Master_Dataset", "EMA_20", "Float / Currency", "20-period Exponential Moving Average", "Quant Engine trend structure"),
            ("Unified_Master_Dataset", "EMA_50", "Float / Currency", "50-period Exponential Moving Average", "Quant Engine trend structure"),
            ("Unified_Master_Dataset", "EMA_200", "Float / Currency", "200-period Exponential Moving Average", "Quant Engine trend structure"),
            ("Unified_Master_Dataset", "Dist_EMA_20_Pct", "Percentage (%)", "Percentage distance from 20 EMA: (P - EMA20) / EMA20 * 100", "Quant Engine trend module"),
            ("Unified_Master_Dataset", "Trend_Regime", "Categorical", "Trend state: bullish (P>=20>50>200), bearish, neutral", "Quant Engine triple EMA rule engine"),
            ("Unified_Master_Dataset", "RSI_14", "Oscillator (0-100)", "14-period Wilder's Relative Strength Index", "Quant Engine momentum module"),
            ("Unified_Master_Dataset", "MACD_Line", "Float", "MACD line: EMA(12) - EMA(26)", "Appel's MACD engine"),
            ("Unified_Master_Dataset", "ATR_14", "Float / Currency", "14-period Average True Range volatility measure", "Wilder's ATR algorithm"),
            ("Unified_Master_Dataset", "Realized_Vol_20D_Pct", "Percentage (%)", "20-day annualized realized volatility: Std(log_ret) * sqrt(252)", "Quant Engine volatility module"),
            ("Unified_Master_Dataset", "Volatility_Regime", "Categorical", "Volatility state: low (<15%), normal, high, extreme (>50%)", "Quant Engine risk classification"),
            ("Unified_Master_Dataset", "Composite_Market_Regime", "Categorical", "Composite Regime: Trend State x Volatility Regime", "Quant Engine Section 21 specification"),
            ("Unified_Master_Dataset", "Composite_Quant_Score", "Score (-1.0 to +1.0)", "Normalized composite quantitative multi-factor score", "Quant Engine multi-factor weighting"),
            ("Unified_Master_Dataset", "Physical_Inventory_Metric", "String", "Official fundamental variable name (e.g. Cushing Stocks, Lower 48)", "FundamentalObservation variable"),
            ("Unified_Master_Dataset", "Physical_Inventory_Value", "Float / Metric", "Observed physical storage level / balance", "EIA / USDA official observation store"),
            ("Unified_Master_Dataset", "COT_Managed_Money_Net", "Integer", "CFTC Disaggregated Managed Money Net Long/Short position", "CFTC official COT report"),
            ("Unified_Master_Dataset", "Top_News_Headline", "Text", "Headline of top market intelligence news wire story on that date", "NewsArticle intelligence stream"),
            ("Unified_Master_Dataset", "News_Sentiment_Score", "Score (-1.0 to +1.0)", "Directional sentiment polarity score", "NewsArticle NLP sentiment engine"),
            ("Unified_Master_Dataset", "Top_Catalyst_Report", "String", "Official scheduled release name (e.g. EIA Weekly Petroleum, WASDE)", "MarketCatalystEvent calendar"),
            ("Unified_Master_Dataset", "Catalyst_Surprise_Delta", "Float / Metric", "Macroeconomic surprise: Actual Release - Survey Consensus", "Economic Surprise Engine"),
            ("Unified_Master_Dataset", "Catalyst_Surprise_Direction", "Categorical", "Surprise classification: BULLISH_SURPRISE, BEARISH_SURPRISE, IN_LINE", "Economic Surprise Engine"),
        ]
        dict_df = pd.DataFrame(dict_rows, columns=["Sheet_Name", "Column_Name", "Data_Type", "Description", "Calculation_Or_Source"])

        # -------------------------------------------------------------
        # 10. Write Multi-Sheet Workbook with OpenPyXL Styles
        # -------------------------------------------------------------
        self.stdout.write(f"  -> Writing multi-sheet Excel workbook to '{output_path}'...")
        wb = openpyxl.Workbook()
        # Remove default sheet
        wb.remove(wb.active)

        # Style Definitions
        header_fill = PatternFill(start_color="1E293B", end_color="1E293B", fill_type="solid")
        header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
        regular_font = Font(name="Calibri", size=10, color="0F172A")
        thin_border = Border(
            left=Side(style="thin", color="E2E8F0"),
            right=Side(style="thin", color="E2E8F0"),
            top=Side(style="thin", color="E2E8F0"),
            bottom=Side(style="thin", color="E2E8F0"),
        )
        center_align = Alignment(horizontal="center", vertical="center")
        left_align = Alignment(horizontal="left", vertical="center")
        right_align = Alignment(horizontal="right", vertical="center")

        def add_sheet_with_styling(sheet_title, df, tab_color="1E293B"):
            ws = wb.create_sheet(title=sheet_title)
            ws.sheet_properties.tabColor = tab_color
            ws.views.sheetView[0].showGridLines = True

            # Write Headers
            headers = list(df.columns)
            ws.append(headers)
            for col_idx in range(1, len(headers) + 1):
                cell = ws.cell(row=1, column=col_idx)
                cell.fill = header_fill
                cell.font = header_font
                cell.alignment = center_align
                cell.border = thin_border
            ws.row_dimensions[1].height = 26

            # Write Data Rows
            for r_idx, row_data in enumerate(df.values, start=2):
                row_vals = [
                    (v.isoformat() if isinstance(v, (date, datetime)) else v)
                    for v in row_data
                ]
                ws.append(row_vals)
                for col_idx in range(1, len(row_vals) + 1):
                    c = ws.cell(row=r_idx, column=col_idx)
                    c.font = regular_font
                    c.border = thin_border
                    val = row_vals[col_idx - 1]
                    if isinstance(val, (int, np.integer)):
                        c.alignment = right_align
                        c.number_format = "#,##0"
                    elif isinstance(val, (float, np.floating)):
                        c.alignment = right_align
                        c.number_format = "#,##0.00"
                    elif isinstance(val, str) and val in ["YES", "NO", "bullish", "bearish", "neutral"]:
                        c.alignment = center_align
                    else:
                        c.alignment = left_align

            # Auto-fit column widths
            for col_idx, col_name in enumerate(headers, start=1):
                max_len = len(str(col_name))
                # Check sample of values
                for row_idx in range(2, min(50, len(df) + 2)):
                    cell_val = str(ws.cell(row=row_idx, column=col_idx).value or "")
                    if len(cell_val) > max_len:
                        max_len = len(cell_val)
                col_letter = get_column_letter(col_idx)
                ws.column_dimensions[col_letter].width = min(45, max(12, max_len + 3))

            ws.freeze_panes = "C2"

        # Sheet 1: Master Unified Dataset
        self.stdout.write("  -> Generating Sheet 1: Unified_Master_Dataset...")
        add_sheet_with_styling("Unified_Master_Dataset", master_df, tab_color="0F172A")

        # Sheet 2: All Contracts OHLCV
        self.stdout.write("  -> Generating Sheet 2: All_Contracts_OHLCV...")
        add_sheet_with_styling("All_Contracts_OHLCV", all_contracts_df, tab_color="2563EB")

        # Sheet 3: Quant Engine Features
        self.stdout.write("  -> Generating Sheet 3: Quant_Engine_Features...")
        quant_sheet_df = quant_df[[
            "observation_date", "commodity__code", "close_clean", "ret_1d", "log_ret_1d",
            "ret_5d", "ret_20d", "ret_accel_1d", "zscore_20d", "percentile_20d", "zscore_60d",
            "ema_20", "ema_50", "ema_200", "dist_ema_20_pct", "dist_ema_50_pct", "dist_ema_200_pct",
            "trend_regime", "rsi_14", "rsi_percentile_60d", "macd_line", "macd_signal", "macd_hist",
            "atr_14", "atr_pct_of_price", "realized_vol_20d_pct", "vol_regime",
            "range_pos_20d_pct", "range_pos_60d_pct", "rvol_20d", "volume_zscore_20d",
            "composite_market_regime", "composite_quant_score"
        ]].copy()
        add_sheet_with_styling("Quant_Engine_Features", quant_sheet_df, tab_color="7C3AED")

        # Sheet 4: Supply & Demand Fundamentals
        self.stdout.write("  -> Generating Sheet 4: Supply_Demand_Fundamentals...")
        fund_sheet_df = pd.DataFrame(fund_rows_for_sheet) if fund_rows_for_sheet else pd.DataFrame(columns=["No_Data"])
        add_sheet_with_styling("Supply_Demand_Fundamentals", fund_sheet_df, tab_color="059669")

        # Sheet 5: News Intelligence
        self.stdout.write("  -> Generating Sheet 5: News_Intelligence...")
        news_sheet_df = pd.DataFrame(news_rows_for_sheet) if news_rows_for_sheet else pd.DataFrame(columns=["No_Data"])
        add_sheet_with_styling("News_Intelligence", news_sheet_df, tab_color="EA580C")

        # Sheet 6: Catalyst Reports
        self.stdout.write("  -> Generating Sheet 6: Catalyst_Reports...")
        cat_sheet_df = pd.DataFrame(catalyst_rows_for_sheet) if catalyst_rows_for_sheet else pd.DataFrame(columns=["No_Data"])
        add_sheet_with_styling("Catalyst_Reports", cat_sheet_df, tab_color="DC2626")

        # Sheet 7: Data Dictionary
        self.stdout.write("  -> Generating Sheet 7: Data_Dictionary...")
        add_sheet_with_styling("Data_Dictionary", dict_df, tab_color="475569")

        # Save Workbook
        wb.save(output_path)
        file_size_mb = round(os.path.getsize(output_path) / (1024 * 1024), 2)
        self.stdout.write(self.style.SUCCESS(
            f"Successfully created unified institutional Excel workbook:\n"
            f"  -> Path: {os.path.abspath(output_path)}\n"
            f"  -> Size: {file_size_mb} MB\n"
            f"  -> Master Rows: {len(master_df):,}\n"
            f"  -> All Contracts Rows: {len(all_contracts_df):,}\n"
            f"  -> Quant Features Rows: {len(quant_sheet_df):,}\n"
            f"  -> Fundamentals Rows: {len(fund_sheet_df):,}\n"
            f"  -> News Articles Rows: {len(news_sheet_df):,}\n"
            f"  -> Catalyst Reports Rows: {len(cat_sheet_df):,}"
        ))
