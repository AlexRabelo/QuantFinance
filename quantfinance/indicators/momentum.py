"""Indicadores de momentum e osciladores."""

from __future__ import annotations

import pandas as pd


def rsi(series: pd.Series, window: int = 14) -> pd.Series:
    """Índice de Força Relativa (RSI)."""
    delta = series.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.rolling(window=window, min_periods=window).mean()
    avg_loss = loss.rolling(window=window, min_periods=window).mean()

    rs = avg_gain / avg_loss.replace({0: pd.NA})
    rsi_series = 100 - (100 / (1 + rs))
    numeric = pd.to_numeric(rsi_series, errors="coerce")
    if pd.api.types.is_float_dtype(numeric.dtype):
        return numeric.fillna(50.0)
    return numeric.astype("float64", copy=False).fillna(50.0)


def stochastic_oscillator(high: pd.Series, low: pd.Series, close: pd.Series, window: int = 14) -> pd.DataFrame:
    """Oscilador estocástico completo (linhas %K e %D)."""
    lowest_low = low.rolling(window=window, min_periods=window).min()
    highest_high = high.rolling(window=window, min_periods=window).max()

    k_percent = ((close - lowest_low) / (highest_high - lowest_low)) * 100
    d_percent = k_percent.rolling(window=3, min_periods=3).mean()

    return pd.DataFrame({"%K": k_percent, "%D": d_percent})


def williams_r(high: pd.Series, low: pd.Series, close: pd.Series, window: int = 14) -> pd.Series:
    """Indicador Williams %R."""
    highest_high = high.rolling(window=window, min_periods=window).max()
    lowest_low = low.rolling(window=window, min_periods=window).min()
    return ((highest_high - close) / (highest_high - lowest_low)) * -100
