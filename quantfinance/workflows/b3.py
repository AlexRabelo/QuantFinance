"""Workflows utilitários para processar arquivos COTAHIST da B3."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, Optional, Callable

import pandas as pd
import yaml

# Importaçã​o opcional dos parsers da B3 para não quebrar em ambientes mínimos de testes
try:  # pragma: no cover - apenas protege import opcional
    from quantfinance.data.b3.cotahist import load_cotahist as _load_cotahist  # type: ignore
except Exception:  # noqa: BLE001 - amplo de propósito para ambientes sem o módulo
    _load_cotahist = None  # type: ignore
from quantfinance.workflows.features.indicators import enrich_dataframe
from quantfinance.workflows.snapshot import snapshot_from_dataframe
from quantfinance.reporting import summarise_snapshot, MarketSnapshot

# Os arquivos COTAHIST devem ser baixados do portal oficial:
# https://www.b3.com.br/pt_br/market-data-e-indices/servicos-de-dados/market-data/historico/mercado-a-vista/series-historicas/
# Salve os .ZIP correspondentes em data/raw/b3.
RAW_DIR = Path("data/raw/b3")
PROCESSED_DIR = Path("data/processed/b3")
CONFIG_PATH = Path("config/tickets.yaml")
CONSOLIDATED_EXCEL = PROCESSED_DIR / "b3_carteira.xlsx"


def load_tickers_from_config(config_path: Path = CONFIG_PATH) -> list[str]:
    if not config_path.exists():
        raise FileNotFoundError(
            f"Arquivo de configuração da carteira não encontrado: {config_path}"
        )
    with config_path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}

    tickers = data.get("b3", {}).get("tickers")

    # Retrocompatibilidade com o formato antigo (carteira_b3.yaml)
    if not tickers:
        tickers = data.get("carteira", {}).get("tickers")

    if not tickers:
        raise ValueError(
            "Nenhum ticker definido na seção 'b3.tickers' do arquivo de carteira."
        )
    return list(dict.fromkeys(ticker.upper() for ticker in tickers))


def iter_cotahist_files(raw_dir: Path = RAW_DIR) -> Iterable[Path]:
    return sorted(raw_dir.glob("COTAHIST_*.ZIP"))


def process_cotahist_archive(
    archive_path: Path,
    tickers: Optional[Iterable[str]] = None,
) -> pd.DataFrame:
    print(f"Processando {archive_path.name}...")
    if _load_cotahist is None:
        raise ImportError(
            "Leitor de COTAHIST indisponível. Certifique-se de ter o módulo "
            "'quantfinance.data.b3.cotahist' ou evite chamar este workflow no ambiente atual."
        )
    return _load_cotahist(archive_path, tickers=tickers)


def persist_raw_history(df: pd.DataFrame, output_dir: Path = PROCESSED_DIR) -> None:
    """Persiste histórico diário por ticker de forma incremental.

    - Cria um arquivo Parquet por ticker em ``output_dir`` com nome ``{TICKER}.parquet``.
    - Faz merge com arquivo existente, mantendo apenas a última ocorrência por data.
    - Garante ordenação por ``Date``.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    if df.empty:
        return

    required = {"Date", "Ticker"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Colunas obrigatórias ausentes: {sorted(missing)}")

    df = df.copy()
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df = df.dropna(subset=["Date", "Ticker"])  # garante integridade mínima

    for ticker, group in df.groupby("Ticker"):
        file_path = output_dir / f"{ticker}.parquet"
        if file_path.exists():
            try:
                existing = pd.read_parquet(file_path)
            except Exception:
                existing = pd.DataFrame()
            combined = pd.concat([existing, group], ignore_index=True)
        else:
            combined = group

        combined["Date"] = pd.to_datetime(combined["Date"], errors="coerce")
        combined = (
            combined.dropna(subset=["Date"]).drop_duplicates(subset=["Date"], keep="last").sort_values("Date").reset_index(drop=True)
        )
        combined.to_parquet(file_path, index=False)


def save_enriched_assets(df: pd.DataFrame, output_dir: Path = PROCESSED_DIR) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    consolidated: dict[str, pd.DataFrame] = {}

    for ticker, group in df.groupby("Ticker"):
        group_sorted = (
            group.sort_values("Date")
            .drop_duplicates(subset=["Date"], keep="last")
            .reset_index(drop=True)
        )
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
    show_summary: bool = True,
) -> dict[str, MarketSnapshot]:
    if tickers is None:
        tickers = load_tickers_from_config()

    archives = list(iter_cotahist_files(raw_dir))
    if not archives:
        print(f"Nenhum arquivo COTAHIST encontrado em {raw_dir}.")
        return {}

    aggregated_frames: list[pd.DataFrame] = []
    for archive_path in archives:
        df = process_cotahist_archive(archive_path, tickers=tickers)
        persist_raw_history(df, output_dir)
        aggregated_frames.append(df)

    if not aggregated_frames:
        print("Nenhum dado processado.")
        return {}

    combined = pd.concat(aggregated_frames, ignore_index=True)
    save_enriched_assets(combined, output_dir)
    snapshots: dict[str, MarketSnapshot] = {}

    for ticker, group in combined.groupby("Ticker"):
        prepared = (
            group.sort_values("Date")
            .drop_duplicates(subset=["Date"], keep="last")
            .reset_index(drop=True)
        )
        snapshots[ticker] = snapshot_from_dataframe(prepared)

    if show_summary and snapshots:
        print("\nResumo dos ativos B3:")
        for ticker in sorted(snapshots):
            print(f"\n{ticker}:\n{summarise_snapshot(snapshots[ticker])}")

    return snapshots


__all__ = [
    "run_b3_pipeline",
    "load_tickers_from_config",
]
