"""Análises de suportes, resistências e níveis relevantes de preço."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Tuple

import numpy as np
import pandas as pd
from scipy.signal import argrelextrema


@dataclass
class PriceLevels:
    """Estrutura para reunir níveis de preço processados."""

    supports: List[float]
    resistances: List[float]
    round_numbers: List[float]
    historical_min: float
    historical_max: float
    rolling_min_52w: float
    rolling_max_52w: float


def _detect_extrema(series: pd.Series, order: int, comparator) -> List[float]:
    """Detecta extremos locais na série utilizando o comparador fornecido."""
    indices = argrelextrema(series.values, comparator, order=order)[0]
    return series.iloc[indices].tolist()


def detect_local_levels(df: pd.DataFrame, column: str = "Close", order: int = 5) -> Tuple[List[float], List[float]]:
    """Retorna suportes e resistências locais usando extremos relativos."""
    supports = _detect_extrema(df[column], order=order, comparator=np.less_equal)
    resistances = _detect_extrema(df[column], order=order, comparator=np.greater_equal)
    return supports, resistances


def detect_round_numbers(series: pd.Series, step: float = 5.0, width: int = 5) -> List[float]:
    """Gera números redondos ao redor da média da série."""
    center = series.mean()
    start = (center // step - width) * step
    return [start + i * step for i in range(2 * width + 1)]


def compute_special_levels(df: pd.DataFrame, column: str = "Close") -> Tuple[float, float, float, float]:
    """Calcula extremos históricos e janelas móveis de 52 semanas."""
    historical_min = float(df[column].min())
    historical_max = float(df[column].max())

    weekly = df[column].resample("W").agg(["min", "max"])
    rolling_min = float(weekly["min"].rolling(window=52, min_periods=1).min().iloc[-1])
    rolling_max = float(weekly["max"].rolling(window=52, min_periods=1).max().iloc[-1])
    return historical_min, historical_max, rolling_min, rolling_max


def consolidate_levels(
    df: pd.DataFrame,
    column: str = "Close",
    order: int = 5,
    round_step: float = 5.0,
    round_width: int = 5,
    grouping_tolerance_pct: float = 0.5,
) -> PriceLevels:
    """Agrupa os principais níveis e devolve uma estrutura consolidada."""
    supports, resistances = detect_local_levels(df, column=column, order=order)
    round_numbers = detect_round_numbers(df[column], step=round_step, width=round_width)
    hist_min, hist_max, roll_min, roll_max = compute_special_levels(df, column=column)

    supports = group_levels(supports, tolerance_pct=grouping_tolerance_pct)
    resistances = group_levels(resistances, tolerance_pct=grouping_tolerance_pct)
    round_numbers = group_levels(round_numbers, tolerance_pct=grouping_tolerance_pct * 2)

    return PriceLevels(
        supports=supports,
        resistances=resistances,
        round_numbers=round_numbers,
        historical_min=hist_min,
        historical_max=hist_max,
        rolling_min_52w=roll_min,
        rolling_max_52w=roll_max,
    )


def group_levels(levels: Iterable[float], tolerance_pct: float = 0.5) -> List[float]:
    """Agrupa níveis que estejam dentro da tolerância percentual informada."""
    levels = sorted(set(levels))
    if not levels:
        return []

    grouped: List[List[float]] = [[levels[0]]]
    for price in levels[1:]:
        last_group = grouped[-1]
        reference = last_group[-1]
        if abs(price - reference) / reference * 100 <= tolerance_pct:
            last_group.append(price)
        else:
            grouped.append([price])

    return [float(np.mean(chunk)) for chunk in grouped]
