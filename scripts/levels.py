"""Módulo de compatibilidade para análises de níveis de preço."""

from __future__ import annotations

from quantfinance.analysis.levels import (
    PriceLevels,
    consolidate_levels,
    detect_local_levels,
    detect_round_numbers,
    compute_special_levels,
    group_levels,
)

__all__ = [
    "PriceLevels",
    "consolidate_levels",
    "detect_local_levels",
    "detect_round_numbers",
    "compute_special_levels",
    "group_levels",
]
