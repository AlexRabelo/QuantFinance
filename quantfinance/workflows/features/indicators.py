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
    on_balance_volume,
    rsi,
    sma,
    stochastic_oscillator,
)


def _ensure_series(df: pd.DataFrame, name: str) -> pd.Series:
    """Garante que df[name] seja uma Série numérica (não um DataFrame)."""
    col = df[name]
    if isinstance(col, pd.DataFrame):
        col = col.iloc[:, 0]
    return pd.to_numeric(col, errors="coerce")


def _sanitize_price_frame(df: pd.DataFrame) -> pd.DataFrame:
    """Normaliza o DataFrame de entrada para evitar problemas de colunas duplicadas.

    - Achata MultiIndex de colunas, caso exista
    - Coalesce colunas duplicadas chave (Open/High/Low/Close/Volume) em uma única Série
    - Remove colunas duplicadas mantendo a primeira ocorrência
    """
    data = df.copy()
    # Flatten MultiIndex if present
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = [str(col[0] if col[0] else col[1]) for col in data.columns]

    def _coalesce(name: str) -> None:
        mask = data.columns == name
        count = int(mask.sum())
        if count <= 1:
            return
        subset = data.loc[:, mask]
        # Converte todas para numérico e escolhe o maior valor por linha (corrige
        # séries duplicadas com escala diferente, p.ex. 34 vs 137)
        numeric_subset = subset.apply(pd.to_numeric, errors="coerce")
        data[name] = numeric_subset.max(axis=1)

    for key in ("Open", "High", "Low", "Close", "Volume"):
        if key in data.columns:
            _coalesce(key)

    # Remove duplicated columns, keep the first occurrence
    data = data.loc[:, ~data.columns.duplicated()]
    return data


def _calc_basic_indicators(df: pd.DataFrame) -> pd.DataFrame:
    enriched = df.copy()
    close = _ensure_series(enriched, "Close")

    enriched["SMA_9"] = sma(close, 9)
    enriched["SMA_21"] = sma(close, 21)
    enriched["SMA_72"] = sma(close, 72)
    enriched["SMA_200"] = sma(close, 200)

    enriched["EMA_9"] = ema(close, 9)
    enriched["EMA_21"] = ema(close, 21)
    enriched["EMA_72"] = ema(close, 72)
    enriched["EMA_200"] = ema(close, 200)

    enriched["Above_SMA_200"] = enriched["Close"] > enriched["SMA_200"]
    enriched["Above_EMA_200"] = enriched["Close"] > enriched["EMA_200"]

    enriched["RSI_14"] = rsi(close, 14)

    macd_df = macd(close)
    enriched = enriched.join(macd_df)

    for std in (2.0, 2.5, 3.0):
        bb = bollinger_bands(close, window=21, num_std=std)
        suffix = str(std).replace(".", "_")
        enriched[f"BB_Middle_{suffix}"] = bb["MiddleBand"]
        enriched[f"BB_Upper_{suffix}"] = bb["UpperBand"]
        enriched[f"BB_Lower_{suffix}"] = bb["LowerBand"]

    if {"High", "Low"}.issubset(enriched.columns):
        high = _ensure_series(enriched, "High")
        low = _ensure_series(enriched, "Low")
        stoch = stochastic_oscillator(high, low, close, window=14)
        enriched["Stoch_%K_14"] = stoch["%K"]
        enriched["Stoch_%D_14"] = stoch["%D"]

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
    # Garante datas timezone-naive para evitar erros de DST em resample
    if "Date" in enriched.columns:
        try:
            dates = pd.to_datetime(enriched["Date"], errors="coerce", utc=True)
            dates = dates.dt.tz_convert(None)
            enriched["Date"] = dates
        except Exception:
            # fallback conservador sem alterar a coluna
            pass
    data = enriched.set_index("Date")
    close = _ensure_series(data, "Close")
    weekly = close.resample("W").agg(["min", "max"])
    rolling_min = weekly["min"].rolling(window=52, min_periods=1).min()
    rolling_max = weekly["max"].rolling(window=52, min_periods=1).max()

    enriched["Min_52w"] = rolling_min.reindex(enriched["Date"]).ffill()
    enriched["Max_52w"] = rolling_max.reindex(enriched["Date"]).ffill()
    enriched["Within_5pct_Max52w"] = enriched["Close"] >= enriched["Max_52w"] * 0.95
    enriched["Within_5pct_Min52w"] = enriched["Close"] <= enriched["Min_52w"] * 1.05
    return enriched


def _calc_returns(df: pd.DataFrame) -> pd.DataFrame:
    enriched = df.copy()
    close = _ensure_series(enriched, "Close")
    enriched["Return_Daily"] = close.pct_change()
    close = close.replace(0, np.nan)
    enriched["Return_Log"] = np.log(close / close.shift())

    high = _ensure_series(enriched, "High") if "High" in enriched.columns else close
    low = _ensure_series(enriched, "Low") if "Low" in enriched.columns else close
    close_prev = close.shift()
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


def _calc_volume_metrics(df: pd.DataFrame) -> pd.DataFrame:
    enriched = df.copy()
    if "Volume" not in enriched.columns:
        return enriched
    volume = _ensure_series(enriched, "Volume").astype(float)
    vol_ma20 = volume.rolling(window=20, min_periods=1).mean()
    enriched["Volume_MA20"] = vol_ma20
    with np.errstate(divide="ignore", invalid="ignore"):
        enriched["Volume_Ratio"] = np.where(vol_ma20 > 0, volume / vol_ma20, np.nan)
    enriched["OBV"] = on_balance_volume(
        enriched["Close"],
        volume,
    )
    return enriched


def _calc_volatility_metrics(df: pd.DataFrame) -> pd.DataFrame:
    enriched = df.copy()
    if "ATR_14" in enriched.columns and "Close" in enriched.columns:
        close = _ensure_series(enriched, "Close").replace(0, np.nan).astype(float)
        atr_norm = enriched["ATR_14"] / close
        enriched["ATR_Pct_14"] = atr_norm * 100.0
    return enriched


def enrich_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    if "Date" not in df.columns:
        raise ValueError("DataFrame precisa incluir coluna 'Date' para enriquecer.")

    # Sanitiza colunas para evitar retornos DataFrame em seleções por nome
    df = _sanitize_price_frame(df)

    enriched = _calc_basic_indicators(df)
    enriched = _calc_extrema_flags(enriched)
    enriched = _calc_52w_metrics(enriched)
    enriched = _calc_returns(enriched)
    enriched = _calc_volume_metrics(enriched)
    enriched = _calc_volatility_metrics(enriched)
    return enriched
