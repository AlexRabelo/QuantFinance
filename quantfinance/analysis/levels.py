"""Support, resistance and price level analysis."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, List

import numpy as np
import pandas as pd
from scipy.signal import argrelextrema


@dataclass
class LevelDetail:
    """Metadata about a detected price level."""

    value: float
    weight: float = 0.0
    count: int = 0
    tags: List[str] = field(default_factory=list)

    def merge(self, other_value: float, increment: float, tag: str) -> None:
        total_weight = self.weight + increment
        if total_weight == 0:
            self.value = other_value
        else:
            self.value = (self.value * self.weight + other_value * increment) / total_weight
        self.weight = total_weight
        self.count += 1
        if tag not in self.tags:
            self.tags.append(tag)


@dataclass
class PriceLevels:
    """Structured collection of relevant price levels."""

    supports: List[float]
    resistances: List[float]
    round_numbers: List[float]
    historical_min: float
    historical_max: float
    rolling_min_52w: float
    rolling_max_52w: float
    support_details: List[LevelDetail] = field(default_factory=list)
    resistance_details: List[LevelDetail] = field(default_factory=list)


def _detect_extrema(series: pd.Series, order: int, comparator) -> List[float]:
    indices = argrelextrema(series.values, comparator, order=order)[0]
    return series.iloc[indices].tolist()


def detect_local_levels(df: pd.DataFrame, column: str = "Close", order: int = 5) -> tuple[List[float], List[float]]:
    """Detect local support and resistance levels using relative extrema."""
    supports = _detect_extrema(df[column], order=order, comparator=np.less_equal)
    resistances = _detect_extrema(df[column], order=order, comparator=np.greater_equal)
    return supports, resistances


def detect_round_numbers(series: pd.Series, step: float = 5.0, width: int = 5) -> List[float]:
    """Generate round numbers around the series mean within a specified width."""
    center = series.mean()
    start = (center // step - width) * step
    return [start + i * step for i in range(2 * width + 1)]


def compute_special_levels(df: pd.DataFrame, column: str = "Close") -> tuple[float, float, float, float]:
    """Compute historical extremes and rolling 52-week extrema."""
    historical_min = float(df[column].min())
    historical_max = float(df[column].max())

    weekly = df[column].resample("W").agg(["min", "max"])
    rolling_min = float(weekly["min"].rolling(window=52, min_periods=1).min().iloc[-1])
    rolling_max = float(weekly["max"].rolling(window=52, min_periods=1).max().iloc[-1])
    return historical_min, historical_max, rolling_min, rolling_max


def _add_candidate(
    candidates: List[LevelDetail],
    value: float,
    *,
    weight: float,
    tag: str,
    tolerance_pct: float,
) -> None:
    if value is None:
        return
    value = float(value)
    if not np.isfinite(value) or value <= 0:
        return

    for detail in candidates:
        reference = detail.value or value
        if reference == 0:
            continue
        if abs(detail.value - value) / abs(reference) * 100 <= tolerance_pct:
            detail.merge(value, weight, tag)
            return

    new_detail = LevelDetail(value=value, weight=weight, count=1, tags=[tag])
    candidates.append(new_detail)


def _finalize_candidates(candidates: List[LevelDetail]) -> List[LevelDetail]:
    return sorted(candidates, key=lambda d: d.value)


def consolidate_levels(
    df: pd.DataFrame,
    column: str = "Close",
    order: int = 5,
    round_step: float = 5.0,
    round_width: int = 5,
    grouping_tolerance_pct: float = 0.5,
) -> PriceLevels:
    """Return a structured view of relevant price levels."""
    supports_local, resistances_local = detect_local_levels(df, column=column, order=order)
    round_numbers = detect_round_numbers(df[column], step=round_step, width=round_width)
    hist_min, hist_max, roll_min, roll_max = compute_special_levels(df, column=column)

    support_details: List[LevelDetail] = []
    resistance_details: List[LevelDetail] = []

    for value in supports_local:
        _add_candidate(
            support_details,
            value,
            weight=1.0,
            tag="swing",
            tolerance_pct=grouping_tolerance_pct,
        )

    for value in resistances_local:
        _add_candidate(
            resistance_details,
            value,
            weight=1.0,
            tag="swing",
            tolerance_pct=grouping_tolerance_pct,
        )

    # Round numbers contribute a smaller weight on ambos lados
    for value in round_numbers:
        _add_candidate(
            support_details,
            value,
            weight=0.3,
            tag="round",
            tolerance_pct=grouping_tolerance_pct * 2,
        )
        _add_candidate(
            resistance_details,
            value,
            weight=0.3,
            tag="round",
            tolerance_pct=grouping_tolerance_pct * 2,
        )

    _add_candidate(
        support_details,
        roll_min,
        weight=3.0,
        tag="rolling_52w",
        tolerance_pct=grouping_tolerance_pct,
    )
    _add_candidate(
        resistance_details,
        roll_max,
        weight=3.0,
        tag="rolling_52w",
        tolerance_pct=grouping_tolerance_pct,
    )

    _add_candidate(
        support_details,
        hist_min,
        weight=4.0,
        tag="historical",
        tolerance_pct=grouping_tolerance_pct,
    )
    _add_candidate(
        resistance_details,
        hist_max,
        weight=4.0,
        tag="historical",
        tolerance_pct=grouping_tolerance_pct,
    )

    support_details = _finalize_candidates(support_details)
    resistance_details = _finalize_candidates(resistance_details)

    supports = [detail.value for detail in support_details]
    resistances = [detail.value for detail in resistance_details]

    return PriceLevels(
        supports=supports,
        resistances=resistances,
        round_numbers=round_numbers,
        historical_min=hist_min,
        historical_max=hist_max,
        rolling_min_52w=roll_min,
        rolling_max_52w=roll_max,
        support_details=support_details,
        resistance_details=resistance_details,
    )


def group_levels(levels: Iterable[float], tolerance_pct: float = 0.5) -> List[float]:
    """Compatibility helper that groups close levels."""
    details: List[LevelDetail] = []
    for value in levels:
        _add_candidate(
            details,
            value,
            weight=1.0,
            tag="generic",
            tolerance_pct=tolerance_pct,
        )
    return [detail.value for detail in _finalize_candidates(details)]
