"""Testes para garantir que a persistência do pipeline B3 não sobrescreve históricos."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from quantfinance.workflows.b3 import persist_raw_history


def _sample_frame(dates: list[str], closes: list[float], ticker: str = "TEST3") -> pd.DataFrame:
    """Cria um DataFrame compatível com a saída do parser COTAHIST."""
    return pd.DataFrame(
        {
            "Date": pd.to_datetime(dates),
            "Ticker": ticker,
            "MarketType": "010",
            "Open": closes,
            "High": closes,
            "Low": closes,
            "Close": closes,
            "Volume": [1_000] * len(closes),
            "Trades": [10] * len(closes),
        }
    )


def test_persist_raw_history_appends_without_overwriting(tmp_path: Path) -> None:
    first_batch = _sample_frame(["2023-01-02"], [10.0])
    second_batch = _sample_frame(["2024-01-02"], [11.0])

    persist_raw_history(first_batch, output_dir=tmp_path)
    persist_raw_history(second_batch, output_dir=tmp_path)

    stored = pd.read_parquet(tmp_path / "TEST3.parquet")

    assert len(stored) == 2
    assert stored["Date"].tolist() == sorted(stored["Date"].tolist())


def test_persist_raw_history_keeps_latest_duplicate(tmp_path: Path) -> None:
    base_batch = _sample_frame(["2023-01-02"], [10.0])
    updated_batch = _sample_frame(["2023-01-02"], [42.0])

    persist_raw_history(base_batch, output_dir=tmp_path)
    persist_raw_history(updated_batch, output_dir=tmp_path)

    stored = pd.read_parquet(tmp_path / "TEST3.parquet")

    assert len(stored) == 1
    assert stored.iloc[0]["Close"] == 42.0
