"""Helpers para consumo do Yahoo Finance."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional

import pandas as pd
import yfinance as yf

from quantfinance.data.core import ensure_datetime


@dataclass
class YahooConfig:
    """Objeto simples de configuração para downloads no Yahoo."""

    tickers: Iterable[str]
    start: Optional[str] = None
    end: Optional[str] = None
    interval: str = "1d"
    auto_adjust: bool = True


def download_history(
    ticker: str,
    start: Optional[str] = None,
    end: Optional[str] = None,
    interval: str = "1d",
    auto_adjust: bool = True,
) -> pd.DataFrame:
    """Baixa candles históricos e padroniza as colunas."""
    data = yf.download(
        ticker,
        start=start,
        end=end,
        interval=interval,
        auto_adjust=auto_adjust,
        progress=False,
    )
    if data.empty:
        raise ValueError(f"O Yahoo Finance não retornou dados para {ticker}")

    data = data.reset_index()
    rename_map = {
        "Date": "Date",
        "Open": "Open",
        "High": "High",
        "Low": "Low",
        "Close": "Close",
        "Adj Close": "AdjClose",
        "Volume": "Volume",
    }
    data = data.rename(columns=rename_map)
    data = ensure_datetime(data, "Date")
    return data


def download_batch(config: YahooConfig) -> dict[str, pd.DataFrame]:
    """Baixa uma lista de tickers e retorna um dicionário ticker -> dados."""
    results: dict[str, pd.DataFrame] = {}
    for ticker in config.tickers:
        results[ticker] = download_history(
            ticker,
            start=config.start,
            end=config.end,
            interval=config.interval,
            auto_adjust=config.auto_adjust,
        )
    return results


def save_to_parquet(data: dict[str, pd.DataFrame], output_dir: str | Path) -> None:
    """Persiste cada ticker em Parquet no diretório indicado."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    for ticker, df in data.items():
        file_path = output_path / f"{ticker.replace('.', '_')}.parquet"
        df.to_parquet(file_path, index=False)
