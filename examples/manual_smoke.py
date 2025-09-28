"""Exemplo manual rápido para validar o pacote QuantFinance."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from quantfinance.data.providers import download_yfinance
from quantfinance.indicators import bollinger_bands, macd, rsi, sma
from quantfinance.workflows import print_snapshot, snapshot_from_dataframe, snapshot_from_excel

DATA_FILE = Path("data/PETR4.xlsx")
RENAME_COLS = {
    "Data": "Date",
    "Abertura": "Open",
    "Máxima": "High",
    "Mínima": "Low",
    "Fechamento": "Close",
    "Volume Financeiro (Milhoes)": "Volume",
}


def main() -> None:
    """Executa um fluxo simples de validação."""
    if DATA_FILE.exists():
        snapshot_local = snapshot_from_excel(DATA_FILE, rename_cols=RENAME_COLS)
        print("Snapshot gerado a partir do arquivo local:")
        print_snapshot(snapshot_local)
    else:
        print("Arquivo local não encontrado, pulando análise do Excel.")

    print("\nBaixando dados do Yahoo Finance...")
    df_yf = download_yfinance("PETR4.SA", start="2023-01-01")

    print("Calculando indicadores básicos (SMA, RSI, MACD, Bandas de Bollinger)...")
    indicators_df = pd.DataFrame({
        "Date": df_yf["Date"],
        "SMA_21": sma(df_yf["Close"], 21),
        "RSI_14": rsi(df_yf["Close"], 14),
    })
    indicators_df = indicators_df.join(macd(df_yf["Close"]))
    indicators_df = indicators_df.join(bollinger_bands(df_yf["Close"]))
    print(indicators_df.tail())

    print("\nGerando snapshot consolidado com dados do Yahoo...")
    snapshot_yf = snapshot_from_dataframe(df_yf)
    print_snapshot(snapshot_yf)


if __name__ == "__main__":
    main()
