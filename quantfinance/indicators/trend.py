"""Indicadores relacionados a tendência."""

from __future__ import annotations

import pandas as pd


def sma(series: pd.Series, window: int) -> pd.Series:
    """Média móvel simples."""
    return series.rolling(window=window, min_periods=window).mean()


def ema(series: pd.Series, window: int) -> pd.Series:
    """Média móvel exponencial."""
    return series.ewm(span=window, adjust=False).mean()


def macd(
    series: pd.Series,
    short_window: int = 12,
    long_window: int = 26,
    signal_window: int = 9,
) -> pd.DataFrame:
    """Indicador MACD (Moving Average Convergence Divergence)."""
    ema_short = ema(series, short_window)
    ema_long = ema(series, long_window)
    macd_line = ema_short - ema_long
    signal_line = macd_line.ewm(span=signal_window, adjust=False).mean()
    histogram = macd_line - signal_line
    return pd.DataFrame(
        {
            "MACD": macd_line,
            "Signal": signal_line,
            "Histogram": histogram,
        }
    )


def average_true_range(high: pd.Series, low: pd.Series, close: pd.Series, window: int = 14) -> pd.Series:
    """Indicador Average True Range (ATR)."""
    high_low = high - low
    high_close = (high - close.shift()).abs()
    low_close = (low - close.shift()).abs()
    true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    return true_range.rolling(window=window, min_periods=window).mean()
