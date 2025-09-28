"""Cálculo de níveis de retração e projeção de Fibonacci."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple

import numpy as np
import pandas as pd
from scipy.signal import argrelextrema


@dataclass
class FibonacciLevels:
    """Agrupa níveis calculados com sua base de referência."""

    levels: Dict[str, float]
    base_high: float
    base_low: float
    high_date: pd.Timestamp
    low_date: pd.Timestamp


DEFAULT_RETRACEMENT_RATIOS = [0.0, 0.236, 0.382, 0.5, 0.618, 0.786, 1.0]
DEFAULT_EXTENSION_RATIOS = [1.272, 1.618, 2.0]


def _positions(series: pd.Series, order: int, comparator) -> set[int]:
    if len(series) < order * 2 + 1:
        return set()
    return set(argrelextrema(series.values, comparator, order=order)[0])


def _find_recent_swing(
    high_series: pd.Series,
    low_series: pd.Series,
    order_short: int = 3,
    order_long: int = 8,
) -> Tuple[float, float, pd.Timestamp, pd.Timestamp]:
    data = pd.concat({"High": high_series, "Low": low_series}, axis=1).dropna()
    if data.empty:
        raise ValueError("Séries insuficientes para detectar swing recente.")

    high_vals = data["High"]
    low_vals = data["Low"]

    high_positions = _positions(high_vals, order_short, np.greater_equal)
    high_positions.update(_positions(high_vals, order_long, np.greater_equal))

    low_positions = _positions(low_vals, order_short, np.less_equal)
    low_positions.update(_positions(low_vals, order_long, np.less_equal))

    if not high_positions or not low_positions:
        high_pos = int(np.nanargmax(high_vals.values))
        low_pos = int(np.nanargmin(low_vals.values))
        return (
            float(high_vals.iloc[high_pos]),
            float(low_vals.iloc[low_pos]),
            high_vals.index[high_pos],
            low_vals.index[low_pos],
        )

    extremes: list[tuple[int, str]] = []
    for pos in high_positions:
        extremes.append((pos, "max"))
    for pos in low_positions:
        extremes.append((pos, "min"))
    extremes.sort(key=lambda item: item[0])

    last_pos, last_kind = extremes[-1]
    opposite_kind = "min" if last_kind == "max" else "max"
    opposite_pos = None
    for pos, kind in reversed(extremes[:-1]):
        if kind == opposite_kind:
            opposite_pos = pos
            break

    if opposite_pos is None:
        high_pos = int(np.nanargmax(high_vals.values))
        low_pos = int(np.nanargmin(low_vals.values))
    else:
        if last_kind == "max":
            high_pos, low_pos = last_pos, opposite_pos
        else:
            high_pos, low_pos = opposite_pos, last_pos

    if high_pos < low_pos:
        high_pos, low_pos = low_pos, high_pos

    return (
        float(high_vals.iloc[high_pos]),
        float(low_vals.iloc[low_pos]),
        high_vals.index[high_pos],
        low_vals.index[low_pos],
    )


def compute_retracements(
    df: pd.DataFrame,
    column: str = "Close",
    lookback: int = 252,
) -> FibonacciLevels:
    close = df[column]
    high = df.get("High", close)
    low = df.get("Low", close)

    data = pd.concat({"Close": close, "High": high, "Low": low}, axis=1).dropna()
    if lookback and lookback > 0:
        data = data.tail(lookback)

    base_high, base_low, high_date, low_date = _find_recent_swing(
        data["High"], data["Low"]
    )

    diff = base_high - base_low if base_high != base_low else 1e-6
    retracements: Dict[str, float] = {}
    for ratio in DEFAULT_RETRACEMENT_RATIOS:
        level = base_high - diff * ratio
        retracements[f"Ret_{int(ratio * 100)}"] = level

    extensions: Dict[str, float] = {}
    for ratio in DEFAULT_EXTENSION_RATIOS:
        level = base_high + diff * (ratio - 1)
        extensions[f"Ext_{int(ratio * 100)}"] = level

    return FibonacciLevels(
        levels={**retracements, **extensions},
        base_high=base_high,
        base_low=base_low,
        high_date=high_date,
        low_date=low_date,
    )
