"""Smoke tests manuais para o pacote QuantFinance."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from quantfinance.data.io import load_excel
from quantfinance.data.providers import download_yfinance
from quantfinance.indicators import bollinger_bands, macd, rsi, sma
from quantfinance.reporting import build_market_snapshot, summarise_snapshot


DATA_FILE = Path("data/PETR4.xlsx")
RENAME_COLS = {
    "Data": "Date",
    "Abertura": "Open",
    "Máxima": "High",
    "Mínima": "Low",
    "Fechamento": "Close",
    "Volume Financeiro (Milhoes)": "Volume",
}


def load_local_example() -> pd.DataFrame:
    """Carrega o exemplo local do diretório data."""
    if not DATA_FILE.exists():
        raise FileNotFoundError(f"Arquivo local não encontrado: {DATA_FILE}")
    df = load_excel(DATA_FILE, date_col="Data", rename_cols=RENAME_COLS)
    return df


def test_yfinance_download() -> pd.DataFrame:
    """Baixa dados do Yahoo Finance para validar credenciais e formatação."""
    df = download_yfinance("PETR4.SA", start="2023-01-01")
    print(df.head())
    print(f"Total linhas Yahoo Finance: {len(df)}\n")
    return df


def compute_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Calcula indicadores básicos e exibe as últimas linhas."""
    data = df.copy()
    data["SMA_21"] = sma(data["Close"], 21)
    data["RSI_14"] = rsi(data["Close"], 14)
    data = data.join(macd(data["Close"]))
    data = data.join(bollinger_bands(data["Close"]))
    print(data.tail()[["Date", "Close", "SMA_21", "RSI_14", "MACD", "Signal", "Histogram", "UpperBand", "LowerBand"]])
    return data


def run_snapshot(df: pd.DataFrame) -> None:
    """Gera e imprime o snapshot consolidado."""
    snapshot = build_market_snapshot(df)
    print(summarise_snapshot(snapshot))


def main() -> None:
    """Executa todas as verificações rápidas."""
    print("Testando leitura do arquivo Excel...")
    df_excel = load_local_example()
    print(df_excel.head())
    print(f"Total linhas Excel: {len(df_excel)}\n")

    print("Testando download via Yahoo Finance...")
    df_yf = test_yfinance_download()

    print("Calculando indicadores na base local...")
    compute_indicators(df_excel)

    print("Calculando indicadores nos dados do Yahoo Finance...")
    compute_indicators(df_yf)

    print("Gerando snapshot consolidado (dados locais)...")
    run_snapshot(df_excel)


if __name__ == "__main__":
    main()
