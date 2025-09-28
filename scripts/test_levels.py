"""Teste manual rápido para detecção de níveis."""

from __future__ import annotations

from pathlib import Path

from quantfinance.analysis import consolidate_levels
from quantfinance.data.io import load_excel


def exemplo_uso_niveis(file_path: str = "data/PETR4.xlsx") -> None:
    """Exibe suportes e resistências usando o arquivo informado."""
    if not Path(file_path).exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {file_path}")

    rename_cols = {"Data": "Date", "Fechamento": "Close"}
    df = load_excel(file_path, date_col="Data", rename_cols=rename_cols)
    df = df.set_index("Date").sort_index()

    levels = consolidate_levels(df[["Close"]])

    print("Suportes locais:", levels.supports)
    print("Resistências locais:", levels.resistances)
    print("Mínima histórica:", levels.historical_min)
    print("Máxima histórica:", levels.historical_max)
    print("Mínima 52 semanas:", levels.rolling_min_52w)
    print("Máxima 52 semanas:", levels.rolling_max_52w)
    print("Números redondos próximos:", levels.round_numbers)


if __name__ == "__main__":
    exemplo_uso_niveis()
