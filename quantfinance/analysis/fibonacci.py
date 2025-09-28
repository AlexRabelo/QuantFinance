"""Cálculo de níveis de retração e projeção de Fibonacci."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

import pandas as pd


@dataclass
class FibonacciLevels:
    """Agrupa níveis calculados com sua base de referência."""

    levels: Dict[str, float]
    base_high: float
    base_low: float


DEFAULT_RETRACEMENT_RATIOS = [0.236, 0.382, 0.5, 0.618, 0.786]
DEFAULT_EXTENSION_RATIOS = [1.272, 1.618, 2.0]


def compute_retracements(
    df: pd.DataFrame,
    column: str = "Close",
    lookback: int = 252,
) -> FibonacciLevels:
    """Calcula retrações e extensões de Fibonacci em uma janela de lookback."""
    swing_window = df[column].tail(lookback)
    base_low = float(swing_window.min())
    base_high = float(swing_window.max())

    diff = base_high - base_low
    retracements = {
        f"Ret_{int(ratio * 100)}": base_high - diff * ratio for ratio in DEFAULT_RETRACEMENT_RATIOS
    }
    extensions = {
        f"Ext_{int(ratio * 100)}": base_high + diff * (ratio - 1) for ratio in DEFAULT_EXTENSION_RATIOS
    }

    return FibonacciLevels(
        levels={**retracements, **extensions},
        base_high=base_high,
        base_low=base_low,
    )
