"""Fluxo pronto para gerar relatórios visuais."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional

import pandas as pd

from quantfinance.data.io import load_excel
from quantfinance.reporting import plot_full_analysis

DEFAULT_RENAME: Dict[str, str] = {
    "Data": "Date",
    "Abertura": "Open",
    "Máxima": "High",
    "Mínima": "Low",
    "Fechamento": "Close",
    "Hora": "Time",
    "Volume": "Volume",
    "Quantidade": "Volume",
    "Volume Financeiro (Milhoes)": "Volume",
}


def render_visual_report(
    source: str | Path,
    rename_cols: Optional[Dict[str, str]] = None,
    date_col: str = "Data",
    output_path: str | Path = "reports/analysis.html",
) -> Path:
    """Carrega um arquivo local e escreve o relatório HTML completo."""
    source = Path(source)
    if not source.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {source}")

    rename_map = DEFAULT_RENAME.copy()
    if rename_cols:
        rename_map.update(rename_cols)

    df = load_excel(source, date_col=date_col, rename_cols=rename_map)
    return plot_full_analysis(df, output_path=output_path)
