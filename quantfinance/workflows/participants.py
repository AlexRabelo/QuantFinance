"""Workflow para processar fluxo de investidores (B3).

Lê os CSVs oficiais/baixados manualmente do site da B3 com saldo
do investidor estrangeiro/institucional e gera saídas consolidadas
em Parquet e Excel.

Entradas esperadas: data/raw/b3/participants/*.csv
Saídas: data/processed/b3/participants_flow.parquet/.xlsx
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import pandas as pd

from quantfinance.data.b3.participants import (
    load_investor_flow_folder,
    summarise_investor_flow,
    save_flow_outputs,
)


RAW_DIR = Path("data/raw/b3/participants")
PROCESSED_DIR = Path("data/processed/b3")


def run_participants_pipeline(
    raw_dir: Path = RAW_DIR,
    output_dir: Path = PROCESSED_DIR,
    *,
    show_summary: bool = True,
) -> Optional[pd.DataFrame]:
    """Carrega todos os CSVs de fluxo, consolida e salva as saídas.

    Retorna o DataFrame consolidado (com métricas 7d/21d/MTD/YTD).
    """
    if not raw_dir.exists():
        print(f"Diretório de entrada não encontrado: {raw_dir}")
        return None

    try:
        flow = load_investor_flow_folder(raw_dir)
    except FileNotFoundError:
        print(f"Nenhum CSV encontrado em {raw_dir}")
        return None

    summary = summarise_investor_flow(flow)
    save_flow_outputs(summary, output_dir)

    if show_summary and not summary.empty:
        latest = summary.tail(5)
        print("Últimas linhas do fluxo de investidores (consolidado):")
        with pd.option_context("display.max_columns", None):
            print(latest)

    return summary


__all__ = [
    "run_participants_pipeline",
]

