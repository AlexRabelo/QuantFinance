"""Indicadores baseados em volatilidade."""

from __future__ import annotations

import pandas as pd


def bollinger_bands(series: pd.Series, window: int = 20, num_std: float = 2.0) -> pd.DataFrame:
    """Calcula as Bandas de Bollinger."""
    moving_average = series.rolling(window=window, min_periods=window).mean()
    moving_std = series.rolling(window=window, min_periods=window).std()
    upper_band = moving_average + moving_std * num_std
    lower_band = moving_average - moving_std * num_std
    return pd.DataFrame(
        {
            "MiddleBand": moving_average,
            "UpperBand": upper_band,
            "LowerBand": lower_band,
        }
    )


def keltner_channel(
    close: pd.Series,
    high: pd.Series,
    low: pd.Series,
    window: int = 20,
    atr_multiplier: float = 2.0,
) -> pd.DataFrame:
    """Calcula o Canal de Keltner usando EMA e ATR."""
    ema = close.ewm(span=window, adjust=False).mean()
    true_range = (high - low).rolling(window=window, min_periods=window).mean()
    upper = ema + atr_multiplier * true_range
    lower = ema - atr_multiplier * true_range
    return pd.DataFrame({"Middle": ema, "Upper": upper, "Lower": lower})
