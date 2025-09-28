"""Funções para enriquecer DataFrames com indicadores técnicos."""

from __future__ import annotations

from typing import Dict

import numpy as np
import pandas as pd
from scipy.signal import argrelextrema

from quantfinance.indicators import (
    bollinger_bands,
    ema,
    macd,
    rsi,
    sma,
)


def _calc_basic_indicators(df: pd.DataFrame) -> pd.DataFrame:
    enriched = df.copy()
    close = enriched["Close"]

    enriched["SMA_9"] = sma(close, 9)
    enriched["SMA_21"] = sma(close, 21)
    enriched["SMA_72"] = sma(close, 72)

    enriched["EMA_9"] = ema(close, 9)
    enriched["EMA_21"] = ema(close, 21)
    enriched["EMA_72"] = ema(close, 72)

    enriched["RSI_14"] = rsi(close, 14)

    macd_df = macd(close)
    enriched = enriched.join(macd_df)

    for std in (2.0, 2.5, 3.0):
        bb = bollinger_bands(close, window=21, num_std=std)
        suffix = str(std).replace(".", "_")
        enriched[f"BB_Middle_{suffix}"] = bb["MiddleBand"]
        enriched[f"BB_Upper_{suffix}"] = bb["UpperBand"]
        enriched[f"BB_Lower_{suffix}"] = bb["LowerBand"]

    return enriched


def _calc_extrema_flags(df: pd.DataFrame, order: int = 3) -> pd.DataFrame:
    enriched = df.copy()
    low_series = enriched.get("Low", enriched["Close"])
    high_series = enriched.get("High", enriched["Close"])

    supports_idx = argrelextrema(low_series.values, np.less_equal, order=order)[0]
    resistances_idx = argrelextrema(high_series.values, np.greater_equal, order=order)[0]

    enriched["IsSupport"] = False
    enriched["IsResistance"] = False

    if supports_idx.size:
        enriched.iloc[supports_idx, enriched.columns.get_loc("IsSupport")] = True
    if resistances_idx.size:
        enriched.iloc[resistances_idx, enriched.columns.get_loc("IsResistance")] = True

    return enriched


def _calc_52w_metrics(df: pd.DataFrame) -> pd.DataFrame:
    enriched = df.copy()
    data = enriched.set_index("Date")
    weekly = data["Close"].resample("W").agg(["min", "max"])
    rolling_min = weekly["min"].rolling(window=52, min_periods=1).min()
    rolling_max = weekly["max"].rolling(window=52, min_periods=1).max()

    enriched["Min_52w"] = rolling_min.reindex(enriched["Date"]).ffill()
    enriched["Max_52w"] = rolling_max.reindex(enriched["Date"]).ffill()
    enriched["Within_5pct_Max52w"] = enriched["Close"] >= enriched["Max_52w"] * 0.95
    enriched["Within_5pct_Min52w"] = enriched["Close"] <= enriched["Min_52w"] * 1.05
    return enriched


def _calc_returns(df: pd.DataFrame) -> pd.DataFrame:
    enriched = df.copy()
    enriched["Return_Daily"] = enriched["Close"].pct_change()

    close = enriched["Close"].replace(0, np.nan)
    enriched["Return_Log"] = np.log(close / close.shift())

    high = enriched.get("High", enriched["Close"])
    low = enriched.get("Low", enriched["Close"])
    close_prev = enriched["Close"].shift()
    tr_components = pd.concat(
        [
            high - low,
            (high - close_prev).abs(),
            (low - close_prev).abs(),
        ],
        axis=1,
    )
    true_range = tr_components.max(axis=1)
    enriched["ATR_14"] = true_range.rolling(window=14, min_periods=14).mean()
    return enriched


def enrich_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    if "Date" not in df.columns:
        raise ValueError("DataFrame precisa incluir coluna 'Date' para enriquecer.")

    enriched = _calc_basic_indicators(df)
    enriched = _calc_extrema_flags(enriched)
    enriched = _calc_52w_metrics(enriched)
    enriched = _calc_returns(enriched)
    return enriched
