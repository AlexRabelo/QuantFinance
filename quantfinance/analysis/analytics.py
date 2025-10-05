"""Utilidades para cálculos agregados (momentum, indicadores compostos)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, Sequence

import numpy as np
import pandas as pd


@dataclass
class MomentumConfig:
    windows: Sequence[int] = (21, 63, 126)
    annualization_factor: int = 252


def compute_momentum_scores(
    data_map: Dict[str, pd.DataFrame],
    config: MomentumConfig | None = None,
) -> pd.DataFrame:
    """Calcula retornos percentuais acumulados por janela.

    Retorna um DataFrame com uma linha por ativo contendo os retornos nas janelas
    e um score médio simples (pode ser customizado externamente).
    """
    config = config or MomentumConfig()
    rows: list[dict[str, float | str]] = []

    for ticker, df in data_map.items():
        if df.empty:
            continue
        frame = df.sort_values("Date")
        if "Close" not in frame.columns:
            continue
        close = frame["Close"].astype(float)
        latest = close.iloc[-1]
        row: dict[str, float | str] = {"Ticker": ticker, "LastClose": latest}
        scores = []
        for window in config.windows:
            if len(close) < window:
                row[f"Return_{window}"] = np.nan
                continue
            window_return = latest / close.iloc[-window] - 1.0
            row[f"Return_{window}"] = window_return
            if not np.isnan(window_return):
                scores.append(window_return)
        row["Score"] = float(np.nanmean(scores)) if scores else np.nan
        rows.append(row)

    result = pd.DataFrame(rows)
    if result.empty:
        return result
    score_cols = [f"Return_{window}" for window in config.windows]
    return result.sort_values("Score", ascending=False).reset_index(drop=True)[
        ["Ticker", "LastClose", *score_cols, "Score"]
    ]


def compute_indicator_snapshot(
    enriched_map: Dict[str, pd.DataFrame],
    columns: Iterable[str],
) -> pd.DataFrame:
    """Extrai indicadores selecionados do último pregão de cada ativo."""
    rows: list[dict[str, float | str]] = []
    columns = list(columns)
    for ticker, df in enriched_map.items():
        if df.empty:
            continue
        latest = df.sort_values("Date").iloc[-1]
        row = {"Ticker": ticker}
        for col in columns:
            row[col] = latest.get(col)
        rows.append(row)
    return pd.DataFrame(rows)
