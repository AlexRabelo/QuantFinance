"""Indicadores guiados por volume."""

from __future__ import annotations

import pandas as pd


def on_balance_volume(close: pd.Series, volume: pd.Series) -> pd.Series:
    """On Balance Volume (OBV)."""
    direction = close.diff().fillna(0)
    signed_volume = volume.where(direction > 0, -volume)
    return signed_volume.cumsum().fillna(0)


def volume_weighted_average_price(close: pd.Series, volume: pd.Series) -> pd.Series:
    """Preço Médio Ponderado por Volume (VWAP) diário simples."""
    cumulative_value = (close * volume).cumsum()
    cumulative_volume = volume.cumsum().replace({0: pd.NA})
    return cumulative_value / cumulative_volume
