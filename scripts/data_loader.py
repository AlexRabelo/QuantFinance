"""Funções de conveniência que encapsulam quantfinance.data."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Iterable, Optional

import pandas as pd

from quantfinance.data import core as core_io
from quantfinance.data.io import carregar_csv, carregar_excel, carregar_profit
from quantfinance.data.providers import (
    download_b3_timeseries,
    download_yfinance,
    download_yfinance_batch,
    load_b3_cotahist,
    load_b3_local_csv,
)
from quantfinance.data.profit.excel import load_profit_workbook

# Reexpõe os helpers com nomes em inglês para scripts/notebooks.
load_csv = carregar_csv
load_excel = carregar_excel
load_profit = carregar_profit


def load_profit_multi_sheet(
    file_path: str | Path,
    rename_cols: Optional[Dict[str, str]] = None,
) -> Dict[str, pd.DataFrame]:
    """Carrega um workbook inteiro do Profit retornando um dicionário por aba."""
    return load_profit_workbook(file_path, rename_cols=rename_cols)


def load_b3_offline(
    file_path: str | Path,
    tickers: Optional[Iterable[str]] = None,
) -> pd.DataFrame:
    """Processa um arquivo COTAHIST para compor um histórico offline."""
    return load_b3_cotahist(file_path, tickers=tickers)


def load_b3_csv(
    file_path: str | Path,
    date_col: str = "Date",
    delimiter: str = ";",
) -> pd.DataFrame:
    """Lê um CSV da B3 e padroniza a coluna de data."""
    return load_b3_local_csv(file_path, date_col=date_col, delimiter=delimiter)


def ensure_datetime(df: pd.DataFrame, column: str) -> pd.DataFrame:
    """Expõe o helper de normalização de datas do módulo core."""
    return core_io.ensure_datetime(df, column)

# Mantém aliases utilizados anteriormente em português.
baixar_yfinance = download_yfinance
baixar_yfinance_lote = download_yfinance_batch
baixar_b3 = download_b3_timeseries
carregar_b3_csv = load_b3_csv
carregar_b3_cotahist = load_b3_offline
carregar_profit_planilha = load_profit_multi_sheet
