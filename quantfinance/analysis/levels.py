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

    def add_tag(self, tag: str, increment: float = 0.0) -> None:
        if tag not in self.tags:
            self.tags.append(tag)
        self.weight += increment


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


def _dropna_series(series: pd.Series) -> pd.Series:
    return series.dropna()


def _detect_supports(series: pd.Series, order: int) -> List[float]:
    series = _dropna_series(series)
    if len(series) < order * 2 + 1:
        return []
    indices = argrelextrema(series.values, np.less_equal, order=order)[0]
    return series.iloc[indices].tolist()


def _detect_resistances(series: pd.Series, order: int) -> List[float]:
    series = _dropna_series(series)
    if len(series) < order * 2 + 1:
        return []
    indices = argrelextrema(series.values, np.greater_equal, order=order)[0]
    return series.iloc[indices].tolist()


def detect_round_numbers(series: pd.Series, step: float = 5.0, width: int = 5) -> List[float]:
    center = series.mean()
    start = (center // step - width) * step
    return [start + i * step for i in range(2 * width + 1)]


def compute_special_levels(df: pd.DataFrame) -> tuple[float, float, float, float]:
    close_series = df["Close"]
    high_series = df.get("High", close_series)
    low_series = df.get("Low", close_series)

    historical_min = float(low_series.min())
    historical_max = float(high_series.max())

    weekly_low = low_series.resample("W").min()
    weekly_high = high_series.resample("W").max()

    rolling_min = float(weekly_low.rolling(window=52, min_periods=1).min().iloc[-1])
    rolling_max = float(weekly_high.rolling(window=52, min_periods=1).max().iloc[-1])
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
    round_step: float = 5.0,
    round_width: int = 5,
    grouping_tolerance_pct: float = 0.5,
) -> PriceLevels:
    if column not in df.columns:
        raise ValueError(f"coluna '{column}' ausente no DataFrame de níveis")

    df = df.sort_index()
    close_series = df[column]
    high_series = df.get("High", close_series)
    low_series = df.get("Low", close_series)

    round_numbers = detect_round_numbers(close_series, step=round_step, width=round_width)
    hist_min, hist_max, roll_min, roll_max = compute_special_levels(df)

    support_details: List[LevelDetail] = []
    resistance_details: List[LevelDetail] = []

    swing_configs = [
        (2, 1.0, "swing_curto"),
        (5, 1.5, "swing_medio"),
        (10, 2.0, "swing_longo"),
    ]

    for swing_order, weight, tag in swing_configs:
        tol = grouping_tolerance_pct * max(1.0, swing_order / 5)
        for value in _detect_supports(low_series, swing_order):
            _add_candidate(
                support_details,
                value,
                weight=weight,
                tag=tag,
                tolerance_pct=tol,
            )
        for value in _detect_resistances(high_series, swing_order):
            _add_candidate(
                resistance_details,
                value,
                weight=weight,
                tag=tag,
                tolerance_pct=tol,
            )

    low_weekly = low_series.resample("W").min()
    high_weekly = high_series.resample("W").max()

    for value in _detect_supports(low_weekly, order=2):
        _add_candidate(
            support_details,
            value,
            weight=3.5,
            tag="swing_semanal",
            tolerance_pct=grouping_tolerance_pct * 2,
        )
    for value in _detect_resistances(high_weekly, order=2):
        _add_candidate(
            resistance_details,
            value,
            weight=3.5,
            tag="swing_semanal",
            tolerance_pct=grouping_tolerance_pct * 2,
        )

    for value in round_numbers:
        _add_candidate(
            support_details,
            value,
            weight=0.3,
            tag="numero_redondo",
            tolerance_pct=grouping_tolerance_pct * 2,
        )
        _add_candidate(
            resistance_details,
            value,
            weight=0.3,
            tag="numero_redondo",
            tolerance_pct=grouping_tolerance_pct * 2,
        )

    _add_candidate(
        support_details,
        roll_min,
        weight=3.0,
        tag="minimo_52s",
        tolerance_pct=grouping_tolerance_pct,
    )
    _add_candidate(
        resistance_details,
        roll_max,
        weight=3.0,
        tag="maximo_52s",
        tolerance_pct=grouping_tolerance_pct,
    )

    _add_candidate(
        support_details,
        hist_min,
        weight=4.0,
        tag="minimo_historico",
        tolerance_pct=grouping_tolerance_pct,
    )
    _add_candidate(
        resistance_details,
        hist_max,
        weight=4.0,
        tag="maximo_historico",
        tolerance_pct=grouping_tolerance_pct,
    )

    latest_price = float(close_series.iloc[-1])

    migrated_resistances: List[LevelDetail] = []
    for detail in resistance_details:
        if "swing_semanal" in detail.tags and detail.value < latest_price:
            detail.add_tag("topo_rompido", increment=2.0)
            support_details.append(detail)
        else:
            migrated_resistances.append(detail)

    support_details = _finalize_candidates(support_details)
    resistance_details = _finalize_candidates(migrated_resistances)

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
    candidates: List[LevelDetail] = []
    for value in levels:
        _add_candidate(
            candidates,
            value,
            weight=1.0,
            tag="generico",
            tolerance_pct=tolerance_pct,
        )
    return [detail.value for detail in _finalize_candidates(candidates)]
