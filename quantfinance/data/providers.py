"""Fachada sobre os provedores de dados especializados."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, Optional

import pandas as pd

from quantfinance.data.core import ensure_datetime
from quantfinance.data.yahoo.client import YahooConfig, download_batch, download_history
from quantfinance.data.b3.cotahist import load_cotahist


def download_yfinance(
    ticker: str,
    start: Optional[str] = None,
    end: Optional[str] = None,
    interval: str = "1d",
    auto_adjust: bool = True,
) -> pd.DataFrame:
    """Mantém a função legada delegando para o módulo Yahoo."""
    return download_history(
        ticker,
        start=start,
        end=end,
        interval=interval,
        auto_adjust=auto_adjust,
    )


def download_yfinance_batch(
    tickers: Iterable[str],
    start: Optional[str] = None,
    end: Optional[str] = None,
    interval: str = "1d",
    auto_adjust: bool = True,
) -> dict[str, pd.DataFrame]:
    """Conveniente para baixar vários tickers de uma vez."""
    config = YahooConfig(
        tickers=tickers,
        start=start,
        end=end,
        interval=interval,
        auto_adjust=auto_adjust,
    )
    return download_batch(config)


def load_b3_local_csv(
    file_path: str | Path,
    date_col: str = "Date",
    delimiter: str = ";",
) -> pd.DataFrame:
    """Lê arquivos CSV baixados manualmente do portal da B3."""
    df = pd.read_csv(file_path, delimiter=delimiter)
    df = ensure_datetime(df, date_col)
    return df.sort_values(date_col).reset_index(drop=True)


def load_b3_cotahist(
    file_path: str | Path,
    tickers: Optional[Iterable[str]] = None,
) -> pd.DataFrame:
    """Exposição simplificada do parser COTAHIST."""
    return load_cotahist(file_path, tickers=tickers)


def download_b3_timeseries(*_: object, **__: object) -> pd.DataFrame:
    """Placeholder para um cliente direto da B3 a ser implementado."""
    raise NotImplementedError(
        "O download direto da B3 ainda não está disponível. Utilize 'load_b3_cotahist' ou "
        "'load_b3_local_csv' com os arquivos oficiais até que um cliente autenticado seja adicionado."
    )
