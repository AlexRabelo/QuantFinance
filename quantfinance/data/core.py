"""Utilidades centrais de dados compartilhadas entre os pipelines."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Iterable, Optional

import pandas as pd


# Tipo auxiliar reutilizado pelas funções de leitura.
ColumnMap = Dict[str, str]


def ensure_datetime(df: pd.DataFrame, column: str) -> pd.DataFrame:
    """Converte a coluna informada para datetime e descarta linhas inválidas."""
    series = pd.to_datetime(df[column], errors="coerce")
    cleaned = df.assign(**{column: series}).dropna(subset=[column])
    return cleaned


def load_csv(
    file_path: str | Path,
    date_col: str = "Date",
    rename_cols: Optional[ColumnMap] = None,
    parse_dates: Optional[Iterable[str]] = None,
) -> pd.DataFrame:
    """Lê um CSV e normaliza a coluna de data."""
    df = pd.read_csv(file_path, parse_dates=parse_dates or [date_col])
    if rename_cols:
        df = df.rename(columns=rename_cols)
        date_col = rename_cols.get(date_col, date_col)
    return ensure_datetime(df, date_col)


def load_excel(
    file_path: str | Path,
    date_col: str,
    rename_cols: Optional[ColumnMap] = None,
    sheet_name: Optional[str] = None,
) -> pd.DataFrame:
    """Lê um Excel usando as convenções do projeto."""
    df = pd.read_excel(file_path, sheet_name=sheet_name)
    df = ensure_datetime(df, date_col)
    if rename_cols:
        df = df.rename(columns=rename_cols)
    return df
