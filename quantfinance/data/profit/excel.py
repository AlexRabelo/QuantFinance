"""Helpers para ingestão de exports do Profit Pro."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional

import pandas as pd

from quantfinance.data.core import ColumnMap, ensure_datetime, load_excel

DEFAULT_RENAME: ColumnMap = {
    "Data": "Date",
    "Hora": "Time",
    "Abertura": "Open",
    "Máxima": "High",
    "Mínima": "Low",
    "Fechamento": "Close",
    "Volume": "Volume",
    "Quantidade": "Volume",
    "Volume Financeiro (Milhoes)": "Volume",
}


def load_profit_sheet(
    file_path: str | Path,
    sheet_name: str,
    rename_cols: Optional[ColumnMap] = None,
    combine_time: bool = True,
) -> pd.DataFrame:
    """Carrega e normaliza uma aba exportada do Profit Pro."""
    rename_map = DEFAULT_RENAME.copy()
    if rename_cols:
        rename_map.update(rename_cols)

    df = load_excel(file_path, date_col="Data", rename_cols=rename_map, sheet_name=sheet_name)

    if combine_time and "Time" in df.columns:
        # Profit exporta Data e Hora separados; mesclamos para obter timestamp completo.
        df["Date"] = df["Date"] + pd.to_timedelta(df["Time"].astype(str))
        df = df.drop(columns=["Time"])

    df = df.sort_values("Date").reset_index(drop=True)
    return df


def load_profit_workbook(
    file_path: str | Path,
    rename_cols: Optional[ColumnMap] = None,
    combine_time: bool = True,
) -> Dict[str, pd.DataFrame]:
    """Carrega todas as abas do workbook e devolve um dicionário ticker -> dados."""
    file_path = Path(file_path)
    workbook = pd.ExcelFile(file_path)
    series_map: Dict[str, pd.DataFrame] = {}
    for sheet in workbook.sheet_names:
        series_map[sheet] = load_profit_sheet(
            file_path=file_path,
            sheet_name=sheet,
            rename_cols=rename_cols,
            combine_time=combine_time,
        )
    return series_map
