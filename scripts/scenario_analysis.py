"""Exemplo de análise de cenário utilizando o pacote QuantFinance."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from quantfinance.data.io import load_excel
from quantfinance.reporting import build_market_snapshot, summarise_snapshot


def main(file_path: str = "data/PETR4.xlsx") -> None:
    """Carrega dados locais, calcula níveis e imprime um resumo de mercado."""
    if not Path(file_path).exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {file_path}")

    rename_cols = {
        "Data": "Date",
        "Abertura": "Open",
        "Máxima": "High",
        "Mínima": "Low",
        "Fechamento": "Close",
        "Volume Financeiro (Milhoes)": "Volume",
    }

    df = load_excel(file_path, date_col="Data", rename_cols=rename_cols)
    snapshot = build_market_snapshot(df)
    print(summarise_snapshot(snapshot))


if __name__ == "__main__":
    main()
