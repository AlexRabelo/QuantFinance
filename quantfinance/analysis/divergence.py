"""Detecção de divergências entre indicador e preço."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

import numpy as np
import pandas as pd
from scipy.signal import argrelextrema


@dataclass
class DivergenceSignal:
    """Representa uma divergência detectada."""

    kind: str
    price_index: pd.Timestamp
    price_level: float
    indicator_level: float


def _extrema(series: pd.Series, order: int, comparator) -> np.ndarray:
    return argrelextrema(series.values, comparator, order=order)[0]


def detect_rsi_divergences(
    prices: pd.Series,
    rsi: pd.Series,
    order: int = 5,
    min_distance: int = 5,
) -> List[DivergenceSignal]:
    """Identifica divergências de RSI em relação ao preço."""
    prices = prices.dropna()
    rsi = rsi.loc[prices.index].dropna()

    bullish: List[DivergenceSignal] = []
    bearish: List[DivergenceSignal] = []

    lows = _extrema(prices, order, np.less_equal)
    highs = _extrema(prices, order, np.greater_equal)

    for idx1, idx2 in zip(lows[:-1], lows[1:]):
        if idx2 - idx1 < min_distance:
            continue
        price1, price2 = prices.iloc[idx1], prices.iloc[idx2]
        rsi1, rsi2 = rsi.iloc[idx1], rsi.iloc[idx2]
        if price2 < price1 and rsi2 > rsi1:
            bullish.append(
                DivergenceSignal(
                    kind="bullish",
                    price_index=prices.index[idx2],
                    price_level=float(price2),
                    indicator_level=float(rsi2),
                )
            )

    for idx1, idx2 in zip(highs[:-1], highs[1:]):
        if idx2 - idx1 < min_distance:
            continue
        price1, price2 = prices.iloc[idx1], prices.iloc[idx2]
        rsi1, rsi2 = rsi.iloc[idx1], rsi.iloc[idx2]
        if price2 > price1 and rsi2 < rsi1:
            bearish.append(
                DivergenceSignal(
                    kind="bearish",
                    price_index=prices.index[idx2],
                    price_level=float(price2),
                    indicator_level=float(rsi2),
                )
            )

    return bullish + bearish
