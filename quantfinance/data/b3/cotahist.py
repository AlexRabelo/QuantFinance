"""Rotinas para montar uma base offline usando arquivos COTAHIST da B3."""

from __future__ import annotations

import io
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional
import zipfile

import pandas as pd

from quantfinance.data.core import ensure_datetime


@dataclass
class CotahistRow:
    """Representa um registro da B3 em formato mais conveniente."""

    date: str
    ticker: str
    market_type: str
    open: float
    high: float
    low: float
    close: float
    volume: int
    trades: int


def _iter_cotahist_lines(file_path: Path) -> Iterable[str]:
    """Itera sobre as linhas de um arquivo TXT ou ZIP de COTAHIST."""
    if file_path.suffix.lower() == ".zip":
        with zipfile.ZipFile(file_path, "r") as archive:
            members = archive.namelist()
            if not members:
                raise ValueError(f"Arquivo {file_path} está vazio")
            with archive.open(members[0], "r") as handle:
                text_stream = io.TextIOWrapper(handle, encoding="latin-1")
                for line in text_stream:
                    yield line.rstrip("\n")
    else:
        with file_path.open("r", encoding="latin-1") as handle:
            for line in handle:
                yield line.rstrip("\n")


def _parse_line(line: str) -> Optional[CotahistRow]:
    """Interpreta uma linha de largura fixa do COTAHIST."""
    record_type = line[0:2]
    if record_type != "01":
        return None

    date = line[2:10]
    ticker = line[12:24].strip()
    market_type = line[24:27].strip()

    def _price(slice_: slice) -> float:
        return float(line[slice_]) / 100.0

    open_price = _price(slice(56, 69))
    high_price = _price(slice(69, 82))
    low_price = _price(slice(82, 95))
    close_price = _price(slice(108, 121))

    trades = int(line[147:152])
    volume = int(line[170:188])

    return CotahistRow(
        date=date,
        ticker=ticker,
        market_type=market_type,
        open=open_price,
        high=high_price,
        low=low_price,
        close=close_price,
        volume=volume,
        trades=trades,
    )


def load_cotahist(
    file_path: str | Path,
    tickers: Optional[Iterable[str]] = None,
) -> pd.DataFrame:
    """Carrega um histórico diário da B3 a partir de um arquivo COTAHIST."""
    file_path = Path(file_path)
    allowed = {ticker.upper() for ticker in tickers} if tickers else None

    rows: list[dict[str, object]] = []
    for raw_line in _iter_cotahist_lines(file_path):
        parsed = _parse_line(raw_line)
        if not parsed:
            continue
        if allowed and parsed.ticker.upper() not in allowed:
            continue
        rows.append(
            {
                "Date": parsed.date,
                "Ticker": parsed.ticker,
                "MarketType": parsed.market_type,
                "Open": parsed.open,
                "High": parsed.high,
                "Low": parsed.low,
                "Close": parsed.close,
                "Volume": parsed.volume,
                "Trades": parsed.trades,
            }
        )

    if not rows:
        raise ValueError(f"Nenhum negócio encontrado em {file_path} para os tickers escolhidos")

    df = pd.DataFrame(rows)
    df = ensure_datetime(df, "Date")
    df = df.sort_values(["Ticker", "Date"]).reset_index(drop=True)
    return df


def save_daily_history(
    df: pd.DataFrame,
    output_dir: str | Path,
    partition_by: str = "Ticker",
) -> None:
    """Persiste o DataFrame em arquivos Parquet particionados."""
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    for ticker, group in df.groupby(partition_by):
        target = output / f"{ticker}.parquet"
        group.to_parquet(target, index=False)


def latest_session(df: pd.DataFrame) -> pd.Timestamp:
    """Retorna a data do último pregão disponível na base."""
    return df["Date"].max()
