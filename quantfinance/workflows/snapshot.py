"""Fluxos prontos para gerar snapshots de mercado."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional

import pandas as pd

from quantfinance.data.io import load_excel
from quantfinance.reporting import MarketSnapshot, build_market_snapshot, summarise_snapshot

DEFAULT_RENAME: Dict[str, str] = {
    "Data": "Date",
    "Abertura": "Open",
    "Máxima": "High",
    "Mínima": "Low",
    "Fechamento": "Close",
    "Hora": "Time",
    "Volume": "Volume",
    "Quantidade": "Volume",
    "Volume Financeiro (Milhoes)": "Volume",
}


def _prepare_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Garante ordenação por data antes de gerar o snapshot."""
    if "Date" in df.columns:
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
        df = df.dropna(subset=["Date"]).sort_values("Date")
    return df


def snapshot_from_dataframe(
    df: pd.DataFrame,
    *,
    macro_context: Optional[Dict[str, float]] = None,
) -> MarketSnapshot:
    """Recebe um DataFrame padronizado e devolve o snapshot consolidado."""
    prepared = _prepare_dataframe(df)
    snapshot = build_market_snapshot(prepared)
    if macro_context:
        snapshot.macro_context = macro_context
    return snapshot


def snapshot_from_excel(
    file_path: str | Path,
    rename_cols: Optional[Dict[str, str]] = None,
    date_col: str = "Data",
) -> MarketSnapshot:
    """Lê um Excel local e gera o snapshot completo imediatamente."""
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {file_path}")

    rename_map = DEFAULT_RENAME.copy()
    if rename_cols:
        rename_map.update(rename_cols)

    df = load_excel(file_path, date_col=date_col, rename_cols=rename_map)
    return snapshot_from_dataframe(df)


def print_snapshot(snapshot: MarketSnapshot) -> None:
    """Imprime o resumo textual do snapshot."""
    print(summarise_snapshot(snapshot))
