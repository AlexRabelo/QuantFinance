"""Workflows utilitários para processar arquivos COTAHIST da B3."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, Optional

import pandas as pd
import yaml

from quantfinance.data.b3.cotahist import load_cotahist, save_daily_history
from quantfinance.workflows.features.indicators import enrich_dataframe

RAW_DIR = Path("data/raw/b3")
PROCESSED_DIR = Path("data/processed/b3")
CONFIG_PATH = Path("config/carteira_b3.yaml")
CONSOLIDATED_EXCEL = PROCESSED_DIR / "b3_carteira.xlsx"


def load_tickers_from_config(config_path: Path = CONFIG_PATH) -> list[str]:
    if not config_path.exists():
        raise FileNotFoundError(
            f"Arquivo de configuração da carteira B3 não encontrado: {config_path}"
        )
    with config_path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    tickers = data.get("carteira", {}).get("tickers", [])
    if not tickers:
        raise ValueError("Nenhum ticker definido em carteira_b3.yaml")
    return tickers


def iter_cotahist_files(raw_dir: Path = RAW_DIR) -> Iterable[Path]:
    return sorted(raw_dir.glob("COTAHIST_*.ZIP"))


def process_cotahist_archive(
    archive_path: Path,
    tickers: Optional[Iterable[str]] = None,
) -> pd.DataFrame:
    print(f"Processando {archive_path.name}...")
    return load_cotahist(archive_path, tickers=tickers)


def persist_raw_history(df: pd.DataFrame, output_dir: Path = PROCESSED_DIR) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    save_daily_history(df, output_dir)


def save_enriched_assets(df: pd.DataFrame, output_dir: Path = PROCESSED_DIR) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    consolidated: dict[str, pd.DataFrame] = {}

    for ticker, group in df.groupby("Ticker"):
        group_sorted = group.sort_values("Date")
        raw_file = output_dir / f"{ticker}_raw.parquet"
        enriched_file = output_dir / f"{ticker}_enriched.parquet"

        group_sorted.to_parquet(raw_file, index=False)
        enriched = enrich_dataframe(group_sorted)
        enriched.to_parquet(enriched_file, index=False)
        consolidated[ticker] = enriched
        print(f"  -> {ticker}: raw/enriched salvos em {output_dir}")

    with pd.ExcelWriter(CONSOLIDATED_EXCEL, engine="openpyxl") as writer:
        for ticker, frame in consolidated.items():
            sheet_name = ticker[:31] if ticker else "Ativo"
            frame.to_excel(writer, sheet_name=sheet_name, index=False)
    print(f"Excel consolidado gerado em {CONSOLIDATED_EXCEL}")


def run_b3_pipeline(
    tickers: Optional[Iterable[str]] = None,
    raw_dir: Path = RAW_DIR,
    output_dir: Path = PROCESSED_DIR,
) -> None:
    if tickers is None:
        tickers = load_tickers_from_config()

    archives = list(iter_cotahist_files(raw_dir))
    if not archives:
        print(f"Nenhum arquivo COTAHIST encontrado em {raw_dir}.")
        return

    aggregated_frames: list[pd.DataFrame] = []
    for archive_path in archives:
        df = process_cotahist_archive(archive_path, tickers=tickers)
        persist_raw_history(df, output_dir)
        aggregated_frames.append(df)

    if not aggregated_frames:
        print("Nenhum dado processado.")
        return

    combined = pd.concat(aggregated_frames, ignore_index=True)
    save_enriched_assets(combined, output_dir)


__all__ = [
    "run_b3_pipeline",
    "load_tickers_from_config",
]
