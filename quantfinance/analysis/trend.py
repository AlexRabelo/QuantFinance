"""Diagnóstico de tendência, rompimentos e regimes."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Mapping, Tuple

import numpy as np
import pandas as pd

from quantfinance.indicators import ema


@dataclass
class TrendSnapshot:
    """Resumo compacto da tendência atual."""

    direction: str
    slope_short: float
    slope_medium: float
    slope_long: float
    crossover: str


@dataclass
class BreakoutSignal:
    """Sinal de rompimento ou falso rompimento."""

    kind: str
    price: float
    reference_level: float
    timestamp: pd.Timestamp


def _slope(values: pd.Series) -> float:
    """Calcula a inclinação de uma série garantindo mínimo de pontos."""
    if len(values.dropna()) < 2:
        return 0.0
    y = values.dropna().values
    x = np.arange(len(y))
    return float(np.polyfit(x, y, 1)[0])


def trend_strength(
    close: pd.Series,
    short_window: int = 9,
    medium_window: int = 21,
    long_window: int = 72,
) -> TrendSnapshot:
    """Avalia direção da tendência via inclinação e empilhamento de médias."""
    ema_short = ema(close, short_window)
    ema_medium = ema(close, medium_window)
    ema_long = ema(close, long_window)

    slope_short = _slope(ema_short.tail(short_window))
    slope_medium = _slope(ema_medium.tail(medium_window))
    slope_long = _slope(ema_long.tail(long_window))

    if slope_short > 0 and slope_medium > 0 and slope_long > 0:
        direction = "uptrend"
    elif slope_short < 0 and slope_medium < 0 and slope_long < 0:
        direction = "downtrend"
    else:
        direction = "sideways"

    if ema_short.iloc[-1] > ema_medium.iloc[-1] > ema_long.iloc[-1]:
        crossover = "bullish_stack"
    elif ema_short.iloc[-1] < ema_medium.iloc[-1] < ema_long.iloc[-1]:
        crossover = "bearish_stack"
    else:
        crossover = "mixed"

    return TrendSnapshot(direction, slope_short, slope_medium, slope_long, crossover)


def trend_by_timeframe(
    close: pd.Series,
    frequencies: Mapping[str, str | None] | None = None,
    short_window: int = 9,
    medium_window: int = 21,
    long_window: int = 72,
) -> Dict[str, TrendSnapshot]:
    """Calcula tendência em múltiplos timeframes a partir da série diária.

    ``frequencies`` mapeia o nome do timeframe para a frequência de resample do
    pandas (ex.: ``{"daily": None, "weekly": "W"}``). ``None`` ou ``"D"``
    mantêm a série original.
    """

    close = close.dropna().sort_index()
    freq_map = frequencies or {"daily": None, "weekly": "W"}
    results: Dict[str, TrendSnapshot] = {}

    for name, freq in freq_map.items():
        if freq in (None, "", "D"):
            series = close
        else:
            series = close.resample(freq).last()
        series = series.dropna()
        if len(series) < max(short_window, medium_window, long_window):
            continue
        results[name] = trend_strength(
            series,
            short_window=short_window,
            medium_window=medium_window,
            long_window=long_window,
        )

    return results


def breakout_signals(
    price: pd.Series,
    support_levels: Tuple[float, ...],
    resistance_levels: Tuple[float, ...],
    tolerance_pct: float = 0.5,
) -> Dict[str, BreakoutSignal | None]:
    """Detecta possíveis rompimentos em relação aos níveis conhecidos."""
    latest_price = float(price.iloc[-1])
    timestamp = price.index[-1]

    def _nearest(levels: Tuple[float, ...]) -> float | None:
        if not levels:
            return None
        return min(levels, key=lambda lvl: abs(lvl - latest_price))

    nearest_support = _nearest(support_levels)
    nearest_resistance = _nearest(resistance_levels)

    breakout_up = None
    if nearest_resistance and latest_price > nearest_resistance * (1 + tolerance_pct / 100):
        breakout_up = BreakoutSignal("breakout_up", latest_price, nearest_resistance, timestamp)

    fake_breakout_up = None
    if nearest_resistance and latest_price < nearest_resistance and price.iloc[-2] > nearest_resistance:
        fake_breakout_up = BreakoutSignal("false_breakout_up", latest_price, nearest_resistance, timestamp)

    breakout_down = None
    if nearest_support and latest_price < nearest_support * (1 - tolerance_pct / 100):
        breakout_down = BreakoutSignal("breakout_down", latest_price, nearest_support, timestamp)

    fake_breakout_down = None
    if nearest_support and latest_price > nearest_support and price.iloc[-2] < nearest_support:
        fake_breakout_down = BreakoutSignal("false_breakout_down", latest_price, nearest_support, timestamp)

    return {
        "breakout_up": breakout_up,
        "false_breakout_up": fake_breakout_up,
        "breakout_down": breakout_down,
        "false_breakout_down": fake_breakout_down,
    }
