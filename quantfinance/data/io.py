"""Camada de compatibilidade com os helpers legados de leitura."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Iterable, Optional

import pandas as pd

from quantfinance.data.core import ensure_datetime, load_csv as _load_csv, load_excel as _load_excel
from quantfinance.data.profit.excel import DEFAULT_RENAME as PROFIT_DEFAULT_RENAME


def load_csv(
    file_path: str | Path,
    date_col: str = "Date",
    rename_cols: Optional[Dict[str, str]] = None,
    parse_dates: Optional[Iterable[str]] = None,
) -> pd.DataFrame:
    """Encapsula o leitor genérico de CSV mantendo a API original."""
    return _load_csv(file_path, date_col=date_col, rename_cols=rename_cols, parse_dates=parse_dates)


def load_excel(
    file_path: str | Path,
    date_col: str,
    rename_cols: Optional[Dict[str, str]] = None,
    sheet_name: Optional[str] = None,
) -> pd.DataFrame:
    """Encapsula o leitor genérico de Excel mantendo a API original."""
    return _load_excel(file_path, date_col=date_col, rename_cols=rename_cols, sheet_name=sheet_name)


def load_profit_export(
    file_path: str | Path,
    rename_cols: Optional[Dict[str, str]] = None,
    date_col: str = "Date",
    time_col: Optional[str] = "Time",
) -> pd.DataFrame:
    """Lê um export do Profit Pro assumindo uma única aba."""
    rename_map = PROFIT_DEFAULT_RENAME.copy()
    if rename_cols:
        rename_map.update(rename_cols)

    df = _load_excel(file_path, date_col="Data", rename_cols=rename_map)

    if time_col and time_col in df.columns:
        df[date_col] = df[date_col] + pd.to_timedelta(df[time_col].astype(str))
        df = df.drop(columns=[time_col])

    df = df.sort_values(date_col).reset_index(drop=True)
    return df


# Mantém aliases em português usados por scripts antigos.
carregar_csv = load_csv
carregar_excel = load_excel
carregar_profit = load_profit_export


def ensure_datetime_column(df: pd.DataFrame, column: str) -> pd.DataFrame:
    """Expõe o helper compartilhado para nomes antigos de função."""
    return ensure_datetime(df, column)
