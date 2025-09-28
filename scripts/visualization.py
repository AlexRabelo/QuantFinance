"""Script de exemplo para gerar visualizações."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from quantfinance.data.io import load_excel
from quantfinance.reporting import plot_full_analysis


def main(file_path: str = "data/PETR4.xlsx") -> None:
    """Gera o gráfico completo a partir de um Excel com histórico de preços."""
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
    output = plot_full_analysis(df)
    print(f"Gráfico salvo em {output}")


if __name__ == "__main__":
    main()
