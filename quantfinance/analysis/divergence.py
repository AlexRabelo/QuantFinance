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
    indicator: str


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
                    indicator="RSI",
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
                    indicator="RSI",
                )
            )

    return bullish + bearish


def detect_obv_divergences(
    prices: pd.Series,
    obv: pd.Series,
    order: int = 5,
    min_distance: int = 5,
) -> List[DivergenceSignal]:
    prices = prices.dropna()
    obv = obv.loc[prices.index].dropna()

    signals: List[DivergenceSignal] = []

    lows = _extrema(prices, order, np.less_equal)
    highs = _extrema(prices, order, np.greater_equal)

    for idx1, idx2 in zip(lows[:-1], lows[1:]):
        if idx2 - idx1 < min_distance:
            continue
        price1, price2 = prices.iloc[idx1], prices.iloc[idx2]
        obv1, obv2 = obv.iloc[idx1], obv.iloc[idx2]
        if price2 < price1 and obv2 > obv1:
            signals.append(
                DivergenceSignal(
                    kind="bullish",
                    price_index=prices.index[idx2],
                    price_level=float(price2),
                    indicator_level=float(obv2),
                    indicator="OBV",
                )
            )

    for idx1, idx2 in zip(highs[:-1], highs[1:]):
        if idx2 - idx1 < min_distance:
            continue
        price1, price2 = prices.iloc[idx1], prices.iloc[idx2]
        obv1, obv2 = obv.iloc[idx1], obv.iloc[idx2]
        if price2 > price1 and obv2 < obv1:
            signals.append(
                DivergenceSignal(
                    kind="bearish",
                    price_index=prices.index[idx2],
                    price_level=float(price2),
                    indicator_level=float(obv2),
                    indicator="OBV",
                )
            )

    return signals


def detect_macd_histogram_divergences(
    prices: pd.Series,
    histogram: pd.Series,
    order: int = 5,
    min_distance: int = 5,
) -> List[DivergenceSignal]:
    prices = prices.dropna()
    histogram = histogram.loc[prices.index].dropna()

    signals: List[DivergenceSignal] = []

    lows = _extrema(prices, order, np.less_equal)
    highs = _extrema(prices, order, np.greater_equal)

    for idx1, idx2 in zip(lows[:-1], lows[1:]):
        if idx2 - idx1 < min_distance:
            continue
        price1, price2 = prices.iloc[idx1], prices.iloc[idx2]
        hist1, hist2 = histogram.iloc[idx1], histogram.iloc[idx2]
        if price2 < price1 and hist2 > hist1:
            signals.append(
                DivergenceSignal(
                    kind="bullish",
                    price_index=prices.index[idx2],
                    price_level=float(price2),
                    indicator_level=float(hist2),
                    indicator="MACD",
                )
            )

    for idx1, idx2 in zip(highs[:-1], highs[1:]):
        if idx2 - idx1 < min_distance:
            continue
        price1, price2 = prices.iloc[idx1], prices.iloc[idx2]
        hist1, hist2 = histogram.iloc[idx1], histogram.iloc[idx2]
        if price2 > price1 and hist2 < hist1:
            signals.append(
                DivergenceSignal(
                    kind="bearish",
                    price_index=prices.index[idx2],
                    price_level=float(price2),
                    indicator_level=float(hist2),
                    indicator="MACD",
                )
            )

    return signals
